# How to install Visual C++ Build tools

Required only on Windows if you plan to use the face-tracking module, which depends on `face_recognition`/`dlib` (see [`src/face_tracking/requirements.txt`](../src/face_tracking/requirements.txt)) and needs a C++ compiler to build from source.

1. Download the installer [here](https://aka.ms/vs/17/release/vs_buildtools.exe)
2. Once downloaded click on the downloaded file and open the installer 
   
   ![icon](./images/build_tools_icon.jpg)
3. During installation, make sure to select "Desktop development with C++" workload
4. ![workload](./images/workload_selection.jpg)