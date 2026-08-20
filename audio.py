import librosa
import numpy as np

def audio_analyst(path):

      #y = samples sr = hz
      y, sr = librosa.load(path, sr=None)
      sample_ref = ["Samples", y, "Sample Rate", sr]

      tempo, bf = librosa.beat.beat_track(y=y, sr=sr)
      bt = librosa.frames_to_time(bf, sr=sr)
      bpm_ref = ["BPM", tempo, "Beat Time", bt]

      mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
      mfcc_delta = librosa.feature.delta(mfccs)
      mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
      mfcc_ref = ["Mfccs", mfccs, "Mfcc Delta", mfcc_delta, "Mfcc Delta2", mfcc_delta2]

      S_db = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
      stft_ref = ["STFT", S_db]

      mel_db = librosa.amplitude_to_db(
          librosa.feature.melspectrogram(y=y, sr=sr), ref=np.max
      )
      mel_ref = ["Mel Spectrogram", mel_db]

      S_C = librosa.feature.spectral_centroid(y=y, sr=sr)
      S_BW = librosa.feature.spectral_bandwidth(y=y, sr=sr)
      S_RO = librosa.feature.spectral_rolloff(y=y, sr=sr)
      S_CT = librosa.feature.spectral_contrast(y=y, sr=sr)
      S_FL = librosa.feature.spectral_flatness(y=y)
      spectral_ref = [
          "Spectral Centroid", S_C,
          "Spectral Bandwidth", S_BW,
          "Spectral Rolloff", S_RO,
          "Spectral Contrast", S_CT,
          "Spectral Flatness", S_FL,
      ]

      ZCR = librosa.feature.zero_crossing_rate(y)
      zcr_ref = ["Zero Cross Rate", ZCR]

      RMS = librosa.feature.rms(y=y)
      rms_ref = ["RMS Energy", RMS]

      chroma = librosa.feature.chroma_stft(y=y, sr=sr)
      y_harmonic = librosa.effects.harmonic(y)
      tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr)
      harmony_ref = ["Chroma", chroma, "Tonnetz", tonnetz]

      onset_env = librosa.onset.onset_strength(y=y, sr=sr)
      onset_ref = ["Onset Strength", onset_env]

      return (
          sample_ref + bpm_ref + mfcc_ref + stft_ref + mel_ref
          + spectral_ref + zcr_ref + rms_ref + harmony_ref + onset_ref
      )