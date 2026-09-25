"""
4CE: on a sovereign install, no library downloads code or models while it runs.

Open WebUI parses an uploaded Excel, Word or PowerPoint file with the
`unstructured` library. Finding spaCy's en_core_web_sm missing, unstructured
fetches the model's wheel from github.com and installs it into site-packages
while the upload is processing. 4CE's egress watch caught it on the first
spreadsheet uploaded: the backend reaching GitHub, and a package appearing
that nobody installed. An air-gapped machine would fail that upload instead.

In offline mode that path is closed here. The attempt fails with the reason,
is written to the audit trail, and the model comes from the offline install
instead. The guard patches the function when the platform first imports the
module, so the backend does not pay for importing spaCy at startup.
"""

import importlib.abc
import logging
import sys

log = logging.getLogger(__name__)

# module -> the function in it that downloads and installs at run time
GUARDED = {"unstructured.nlp.tokenize": "_install_spacy_model"}

# What was refused since the backend started, for the sovereignty page.
refused: list[str] = []


def _refusal(module: str, function: str):
    def refuse(*args, **kwargs):
        what = f"{module}.{function}"
        refused.append(what)
        log.warning("4CE offline mode refused a run-time download: %s", what)
        try:
            from open_webui.utils.fource_audit import record

            record("download.refused", library=module.split(".")[0], call=function)
        except Exception:
            pass
        raise RuntimeError(
            f"4CE is in offline mode, so {module.split('.')[0]}'s attempt to download a model "
            f"while running ({what}) was refused. Install the model with the rest of 4CE's "
            "offline install - see 'Offline install' in 4ce/docs/HOW_TO_RUN.md."
        )

    refuse.__fource_guard__ = True
    return refuse


class _Guard(importlib.abc.MetaPathFinder):
    """Patches a guarded module the moment it is first imported."""

    def find_spec(self, fullname, path, target=None):
        if fullname not in GUARDED:
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, "find_spec"):
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"):
                continue
            original = spec.loader.exec_module

            def exec_module(module, _original=original, _name=fullname):
                _original(module)
                setattr(module, GUARDED[_name], _refusal(_name, GUARDED[_name]))

            spec.loader.exec_module = exec_module
            return spec
        return None


def guard() -> list[str]:
    """Close the run-time download paths 4CE knows of; returns them."""
    for name, function in GUARDED.items():
        module = sys.modules.get(name)
        if module is not None and hasattr(module, function):
            setattr(module, function, _refusal(name, function))
    if not any(isinstance(finder, _Guard) for finder in sys.meta_path):
        sys.meta_path.insert(0, _Guard())
    return list(GUARDED)
