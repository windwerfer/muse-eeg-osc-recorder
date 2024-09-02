import os
import subprocess
import time

# pkg install pulseaudio mpv socat

def change_volume(volume, ipc_path):
    """
    Change the volume of the audio playback using mpv's IPC server.

    Parameters:
    - volume (int): The desired volume level (0 to 100).
    - ipc_socket (str): The path to the IPC socket used by mpv.
    """
    # Ensure the volume is within the valid range
    if not (0 <= volume <= 100):
        raise ValueError("Volume must be between 0 and 100.")

    # JSON command to set the volume
    command = f'{{"command": ["set_property", "volume", {volume}]}}'

    # Use socat to send the command to the mpv IPC server
    try:
        subprocess.run(
            f'echo \'{command}\' | socat - {ipc_path}',
            shell=True,
            check=True
        )
        print(f"Volume set to {volume}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to change volume: {e}")

def play_sound(filename, volume=50, background=False):
    """
    Play sound using mpv with the option to run in the background.

    Parameters:
    - filename (str): The path to the audio file to play.
    - background (bool): If True, run mpv as a background process.
    """
    ipc_path = os.path.expanduser("~/mpv_socket")

    # Command to play the sound using mpv with an IPC server
    cmd = f"mpv --no-video --volume={volume} --input-ipc-server={ipc_path} \"{filename}\""

    # Start mpv in a subprocess
    if background:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            while process.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping playback...")
            process.terminate()
        finally:
            # Cleanup the IPC socket
            if os.path.exists(ipc_path):
                os.remove(ipc_path)

    return ipc_path

# Main execution
if __name__ == "__main__":

    mp3_file = "audio/boreal_owl.mp3"

    if os.path.exists(mp3_file):
        ipc_path = play_sound(mp3_file, background=True)
        time.sleep(4)
        change_volume(100, ipc_path)
        time.sleep(10)
    else:
        print("The specified audio file does not exist.")
