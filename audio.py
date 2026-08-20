import librosa
import numpy as np

def audio_analyst(path):

      #y = samples sr = hz
      y, sr = librosa.load(path, sr=None)
      sample_ref = ["Samples", y,"Sample Rate",sr]

      tempo, bf = librosa.beat.beat_track(y=y, sr=sr)
      bt = librosa.frames_to_time(bf, sr=sr)
      bpm_ref = ["BPM",tempo,"Beat Time",bt]

      mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
      mfccs = ["Mfccs",mfccs]

      S_db = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
      S_db = ["STFT", S_db]

      S_C = librosa.feature.spectral_centroid(y=y, sr=sr)
      S_C = ["Spectral Centroid", S_C]

      ZCR = librosa.feature.zero_crossing_rate(y) 
      ZCR = ["Zero Cross Rate", ZCR]

      return sample_ref + bpm_ref + mfccs + S_db + S_C + ZCR