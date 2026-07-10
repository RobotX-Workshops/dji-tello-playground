# Face Tracking

To use the face tracking, we need to install additional dependencies.

If you're on Windows, you need to have installed Visual Studio with C++ build tools
see [this guide](../../docs/installing_vs_build_tools.md) on how to install them.

Then in the CLI in the face_tracking directory run
```bash
pip install -r requirements.txt
```

## Running the face tracking

First, lets do a sanity check to see if the face tracking works. Run the following command in the CLI in the face_tracking directory
```bash
python sanity_check.py
```



To run full face tracking with the drone, use the [`follow_face.py`](../example_exercises/follow_face.py) exercise script. As noted in the [example exercises guide](../example_exercises/README.md), it must be run from the `src` directory:
```bash
python example_exercises/follow_face.py
```