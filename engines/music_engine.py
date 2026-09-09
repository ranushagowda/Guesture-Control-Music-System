"""
engines/music_engine.py  —  Phase 3
====================================
Real audio playback using sounddevice + soundfile.
Runs in a QThread so the GUI never blocks.

Signals (emit to GUI)
---------------------
sig_song_changed(index, name, duration)
sig_progress(elapsed, duration)
sig_state_changed(state_str)
sig_volume_changed(float)
sig_error(str)
"""
from __future__ import annotations
import threading, time
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread, QTimer
import sounddevice as sd
import soundfile as sf
import numpy as np
from core.logger import get_logger
from utils.file_utils import scan_audio_files, short_name

log = get_logger(__name__)


class _PlayerThread(threading.Thread):
    """Low-level audio thread: streams one file, supports pause/stop/volume."""

    def __init__(self, path: str, volume: float, on_finish):
        super().__init__(daemon=True)
        self.path      = path
        self.volume    = volume          # 0.0-1.0, read live
        self.paused    = False
        self.muted     = False
        self.stop_flag = False
        self.position  = 0              # current frame index
        self.total_frames = 0
        self.samplerate   = 44100
        self._on_finish   = on_finish
        self._lock        = threading.Lock()

    def run(self):
        try:
            data, sr = sf.read(self.path, dtype="float32", always_2d=True)
        except Exception as e:
            log.error("Cannot read %s: %s", self.path, e)
            self._on_finish()
            return

        self.samplerate   = sr
        self.total_frames = len(data)
        chunk = 1024

        def cb(outdata, frames, _t, _s):
            if self.stop_flag or self.paused:
                outdata[:] = 0
                return
            end   = self.position + frames
            block = data[self.position:end]
            if len(block) < frames:
                pad   = np.zeros((frames - len(block), data.shape[1]), dtype=np.float32)
                block = np.vstack([block, pad])
                self.stop_flag = True
            # channel match
            if outdata.shape[1] != block.shape[1]:
                block = (block.mean(axis=1, keepdims=True)
                         if outdata.shape[1] == 1
                         else np.repeat(block, 2, axis=1))
            vol = 0.0 if self.muted else self.volume
            outdata[:] = (block * vol).astype(np.float32)
            self.position = min(end, self.total_frames)

        try:
            with sd.OutputStream(samplerate=sr, channels=data.shape[1],
                                  blocksize=chunk, callback=cb):
                while not self.stop_flag:
                    time.sleep(0.05)
        except Exception as e:
            log.error("Audio stream error: %s", e)
        finally:
            self._on_finish()

    def seek(self, ratio: float):
        self.position = int(ratio * self.total_frames)

    @property
    def elapsed(self) -> float:
        return self.position / max(self.samplerate, 1)

    @property
    def duration(self) -> float:
        return self.total_frames / max(self.samplerate, 1)


class MusicEngine(QObject):
    sig_song_changed  = Signal(int, str, float)
    sig_progress      = Signal(float, float)
    sig_state_changed = Signal(str)
    sig_volume_changed= Signal(float)
    sig_playlist_ready= Signal(list)
    sig_playlist_updated = Signal(list)   # emitted when a song is added
    sig_error         = Signal(str)

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self._cfg     = cfg
        self._songs: list[Path] = []
        self._index   = 0
        self._volume  = float(cfg.music.default_volume)
        self._shuffle = bool(cfg.music.shuffle)
        self._repeat  = bool(cfg.music.repeat)
        self._muted   = False
        self._player: _PlayerThread | None = None
        self._history: list[int] = []
        self._saved_position: int = 0   # frame position saved on stop
        self._hard_stopped: bool = False  # True when stopped by Fist gesture
        self._play_gen: int = 0          # incremented on every stop; stale callbacks ignored

        # Progress ticker
        self._ticker = QTimer()
        self._ticker.setInterval(500)
        self._ticker.timeout.connect(self._tick_progress)

    # ── Initialise ────────────────────────────────────────────────────────────

    def load_library(self):
        self._songs = scan_audio_files(
            self._cfg.music.song_dir,
            self._cfg.music.supported_formats,
        )
        names = [short_name(s) for s in self._songs]
        self.sig_playlist_ready.emit(names)
        log.info("MusicEngine: %d songs loaded", len(self._songs))
        if self._songs:
            self._index = 0
            # Do NOT auto-play — wait for gesture or user action

    # ── Playback controls ─────────────────────────────────────────────────────

    def play(self, index: int | None = None):
        """Start or resume. Clears hard_stopped so Fist-stop is released."""
        if not self._songs:
            self.sig_error.emit("No songs in library.")
            return

        self._hard_stopped = False  # Open Hand / Rock / Peace all release the stop

        # If a specific song is requested, switch to it
        if index is not None:
            self._index = index
            self._stop_player()

        # If already playing the current song, just ensure it's not paused
        if self._player and not self._player.stop_flag:
            if self._player.paused:
                self._player.paused = False
                self.sig_state_changed.emit("PLAYING")
            return  # already playing — do nothing

        # Start fresh, restore saved position if resuming same song
        self._stop_player()
        path = str(self._songs[self._index])
        gen = self._play_gen
        self._player = _PlayerThread(path, self._volume, lambda: self._on_song_finished(gen))
        self._player.muted = self._muted
        if index is None and self._saved_position > 0:
            self._player.position = self._saved_position  # resume from where stopped
        self._saved_position = 0
        self._player.start()
        name = short_name(self._songs[self._index])
        try:
            info = sf.info(path)
            dur  = info.frames / info.samplerate
        except Exception:
            dur = 0.0
        self.sig_song_changed.emit(self._index, name, dur)
        self.sig_state_changed.emit("PLAYING")
        self._ticker.start()
        # Only append to history if this is a genuinely new song
        if not self._history or self._history[-1] != self._index:
            self._history.append(self._index)
        log.info("Playing [%d] %s", self._index, name)

    def stop(self):
        """Hard stop by Fist — music stays stopped until play() is called."""
        self._hard_stopped = True
        if self._player:
            self._saved_position = self._player.position
        self._stop_player()
        self.sig_state_changed.emit("STOPPED")
        log.info("Hard stop. Waiting for Open Hand / Rock / Peace to resume.")

    def pause_resume(self):
        if not self._player:
            self.play(self._index)
            return
        self._player.paused = not self._player.paused
        state = "PAUSED" if self._player.paused else "PLAYING"
        self.sig_state_changed.emit(state)

    def next_song(self):
        """Always advance to index+1 in list order, wraps around."""
        if not self._songs:
            return
        self._hard_stopped = False
        self._index = (self._index + 1) % len(self._songs)
        self._saved_position = 0
        self._stop_player()
        self.play()

    def previous_song(self):
        """Go back to the song played before the current one."""
        if not self._songs:
            return
        self._hard_stopped = False
        # history tail is always the current song; peek one before it
        if len(self._history) >= 2:
            self._history.pop()              # discard current
            self._index = self._history[-1]  # previous song (keep in history)
        else:
            self._index = (self._index - 1) % len(self._songs)
        self._saved_position = 0
        self._stop_player()
        self.play()

    def set_volume(self, v: float):
        self._volume = max(0.0, min(1.0, v))
        if self._player:
            self._player.volume = self._volume
        self.sig_volume_changed.emit(self._volume)

    def toggle_mute(self):
        self._muted = not self._muted
        if self._player:
            self._player.muted = self._muted

    def toggle_shuffle(self):
        self._shuffle = not self._shuffle

    def toggle_repeat(self):
        self._repeat = not self._repeat

    def seek(self, ratio: float):
        if self._player:
            self._player.seek(ratio)

    def seek_delta(self, seconds: float):
        """Skip forward (positive) or rewind (negative) by seconds."""
        if self._player and self._player.total_frames > 0:
            sr      = self._player.samplerate
            new_pos = self._player.position + int(seconds * sr)
            new_pos = max(0, min(self._player.total_frames - 1, new_pos))
            self._player.position = new_pos

    def add_song(self, path: str):
        """Copy file to Song/ folder and append to playlist."""
        import shutil
        src = Path(path).resolve()
        dest_dir = Path(self._cfg.music.song_dir).resolve()
        if not src.exists():
            self.sig_error.emit(f"File not found: {path}")
            return
        if src.suffix.lower() not in {".mp3", ".wav", ".ogg", ".flac", ".aac"}:
            self.sig_error.emit(f"Unsupported file type: {src.suffix}")
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = (dest_dir / src.name).resolve()
        if not str(dest).startswith(str(dest_dir)):
            self.sig_error.emit("Invalid file path.")
            return
        if dest != src:
            shutil.copy2(src, dest)
        if dest not in self._songs:
            self._songs.append(dest)
            names = [short_name(s) for s in self._songs]
            self.sig_playlist_updated.emit(names)
            log.info("Song added: %s", dest.name)

    def select_song(self, index: int):
        self.play(index)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _stop_player(self):
        self._play_gen += 1          # invalidate any in-flight _on_finish callbacks
        if self._player:
            self._player.stop_flag = True
            self._player = None
        self._ticker.stop()

    def _on_song_finished(self, gen: int = -1):
        """Called by _PlayerThread when audio reaches the end naturally."""
        if gen != self._play_gen or self._hard_stopped or not self._songs:
            return
        if self._repeat:
            self.play(self._index)
        else:
            # Always sequential auto-advance
            self._index = (self._index + 1) % len(self._songs)
            self._saved_position = 0
            self._stop_player()
            self.play()

    def _tick_progress(self):
        if self._player and not self._player.paused:
            self.sig_progress.emit(self._player.elapsed, self._player.duration)

    @property
    def current_path(self) -> str:
        if self._songs:
            return str(self._songs[self._index])
        return ""

    @property
    def volume(self) -> float:
        return self._volume
