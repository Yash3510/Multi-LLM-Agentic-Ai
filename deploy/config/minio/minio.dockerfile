# MinIO's community edition is archived and publishes source only, so this builds its last
# release, unmodified, from the upstream tag. It gets no upstream security patches: it is for
# development. The patch source for pilots is ADR-0025's decision
# (see docs/research/minio-patch-source.md).

FROM golang:1.24-alpine@sha256:8bee1901f1e530bfb4a7850aa7a479d17ae3a18beb6e09064ed54cfd245b7191 AS build
ARG MINIO_RELEASE=RELEASE.2025-10-15T17-29-55Z
ARG MINIO_COMMIT=9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a
RUN apk add --no-cache git
RUN git clone --depth 1 --branch "$MINIO_RELEASE" https://github.com/minio/minio.git /src
WORKDIR /src
# The tag must still point at the commit recorded in deploy/third-party/minio/SOURCE.
RUN test "$(git rev-parse HEAD)" = "$MINIO_COMMIT"
# The same build as upstream's Makefile: static, with the release's version stamped in.
RUN CGO_ENABLED=0 go build -tags kqueue -trimpath \
    -ldflags "$(go run buildscripts/gen-ldflags.go)" -o /out/minio

FROM alpine:3.22@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8
RUN addgroup -S minio && adduser -S -G minio minio && mkdir /data && chown minio:minio /data
COPY --from=build /out/minio /usr/bin/minio
USER minio
EXPOSE 9000 9001
ENTRYPOINT ["/usr/bin/minio"]
CMD ["server", "/data", "--console-address", ":9001"]
