Record raw eeg, ppg (heart rate), acc (movement) values from the muse app or mindmonitor through the osc stream that these apps (can) send.

they can be directly imported into EegLab for further analysis

You need to setup the muse app/mindmonitor to stream the eeg data (as a osc stream) first:
  a) Muse app:
    -go to the 'Me' tab (bottom of the app)
    -top right corner click on the the wheel icon (=enter settings)
    -scroll to the very bottom
    -click on 'osc output'
    -change the ip address to 127.0.0.1
    -change port to 5000
    -check the toggle for: Streaming Enabled (should move to the right and turn green)
  b) mindmonitor app
    -at the bottom of the screen click on the wheel icon (=enter settings)
    -scroll down to 'osc stream Target ip' and set to 127.0.0.1
    -underneath set 'osc stream port' to 5000
    -set 'osc stream brainwaves' to 'all values' (toggle off)

the next part is, if you want to run it form your phone:
  -download and install termux: apk package from https://github.com/termux/termux-app/releases/download/v0.118.1/termux-app_v0.118.1+github-debug_universal.apk or use the f-droid version (playstore is not recommended by the developer, and will probably not work well)
  -run: 
```
termux-setup-storage
pkg update
yes | pkg upgrade  # automatically send yes to install pa
pkg upgrade
pkg install python3 python-numpy matplotlib pulseaudio mpv build-essential 
pip install python-osc psutil
```

this should make it possible to run all of this in termux (except graphs, because it does not have a xwindow). for windows / linux / mac
- install python
- after installing pyton, open a terminal and run:
```
pip install wheel python-osc psutil numpy matplotlib
```

open a terminal and go to the script folder and run (starts the recorder)
```
python write_osc_to_files.py
```
it will generate the recoded files in the folder osc_out.

to start recoding, go to the muse app and start a meditation. it will automatically stream the data to termux and if the script is running it will record them. a new file will be created if there was a 5min pause between sessions.

or in mindmonitor click on the 4th symbol in the bottom row (looks like a wifi signal) and it will start streaming the muse data.

the recorder script and the muse app do not need to be on the same device. could be a computer for recoding too. just need to set the correct ip address (address of the computer you want to record the script on) in the muse app / mindmonitor.

Bonus: there is a small bio feedback part, that plays a mp3 file whenever you get sleepy and your head nodds (uses the accelerometer data). to enable it start programm with

```
python write_osc_to_files.py --feedback_acc
```

Future maybe: some graphs to be generated, but not yet done (that why the python library matplotlib is needed)