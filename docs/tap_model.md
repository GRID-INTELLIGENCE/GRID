# Visual–Acoustic Tap Model (POC)

Objective:
Translate an unseen studio space into measurable descriptors using a single tap impulse.

Usage (CLI):

- Simulation only:
  python scripts/tap_report.py --length 5 --width 4 --height 3 --source 2.5 2 1.5

- From WAV recording (first 200ms analyzed):
  python scripts/tap_report.py --from-wav examples/tap.wav --peak-prominence 0.05

Notes:
- `requirements.txt` lists optional deps (`soundfile`, `scipy`) required for `--from-wav`.
- Model approximations: early reflections treated as single-bounce spikes, amplitude ~ tap_energy * R / d^2.
