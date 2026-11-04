// The toolbar's "Replay motion": every section that demonstrates motion re-runs it when count changes.
let count = $state(0);

export const replay = {
  get count(): number {
    return count;
  },
  run() {
    count += 1;
  },
};
