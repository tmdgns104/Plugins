import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
from scipy.signal import periodogram
import pygame
import time
from datetime import datetime

class WavTestPlayer:
    def __init__(self, filename, repeat=3, delay=2, log=True):
        self.filename = filename
        self.repeat = repeat
        self.delay = delay
        self.log = log
        pygame.mixer.init()

    def play_once(self):
        try:
            pygame.mixer.music.load(self.filename)
            pygame.mixer.music.play()
            if self.log:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ▶ 재생 시작")

            while pygame.mixer.music.get_busy():
                time.sleep(0.2)

            if self.log:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 재생 완료")

        except Exception as e:
            print(f"[ERROR] 재생 실패: {e}")

    def run_test(self):
        for i in range(self.repeat):
            print(f"\n=== 반복 {i + 1} / {self.repeat} ===")
            self.play_once()
            if i < self.repeat - 1:
                time.sleep(self.delay)


class AudioAnalyzer:
    def __init__(self, filename):
        self.filename = filename              # 분석할 WAV 파일 경로
        self.rate = None                      # 샘플링 레이트 (Hz)
        self.data = None                      # 오디오 샘플 데이터 (모노)
        self.signal_power = None              # 1kHz 대역 신호 전력
        self.noise_power = None               # 신호를 제외한 노이즈 전력
        self.snr_db = None                    # SNR 결과 (dB)
        self.sinad_db = None                  # SINAD 결과 (dB)

    def load_wave(self):
        self.rate, data = wav.read(self.filename)       # 샘플링 레이트와 데이터 읽기
        if len(data.shape) > 1:                          # 스테레오이면
            data = data.mean(axis=1)                     # 두 채널 평균내어 모노 변환
        self.data = data                                 # 변환된 데이터를 클래스에 저장

    def compute_signal_noise(self, tone_band=(990, 1010)):
        if self.data is None:
            self.load_wave()                             # 데이터가 없으면 WAV 파일 로드

        # FFT 기반 파워 스펙트럼 계산
        freqs, psd = periodogram(self.data, fs=self.rate, scaling='spectrum')

        # 1kHz 대역 필터링 마스크 생성
        band_mask = (freqs >= tone_band[0]) & (freqs <= tone_band[1])

        # 신호 전력: 1kHz 대역의 전력 합
        self.signal_power = np.sum(psd[band_mask])

        # 노이즈 전력: 전체 전력에서 신호 전력 제외
        self.noise_power = np.sum(psd) - self.signal_power

    def compute_snr(self):
        if self.signal_power is None or self.noise_power is None:
            self.compute_signal_noise()

        epsilon = 1e-12                                       # 0 나누기 방지용 소수
        signal_db = 10 * np.log10(self.signal_power + epsilon)  # 신호 전력을 dB로 변환
        noise_db = 10 * np.log10(self.noise_power + epsilon)    # 노이즈 전력을 dB로 변환
        self.snr_db = signal_db - noise_db                      # SNR = 신호 - 노이즈 (dB 차이)

        return self.snr_db

    def compute_sinad(self):
        if self.signal_power is None or self.noise_power is None:
            self.compute_signal_noise()

        epsilon = 1e-12
        self.sinad_db = 10 * np.log10(self.signal_power / (self.noise_power + epsilon))  # SINAD 공식

        return self.sinad_db

    def plot_noise_sinad(self):
        if self.signal_power is None or self.noise_power is None:
            self.compute_signal_noise()
        if self.snr_db is None:
            self.compute_snr()
        if self.sinad_db is None:
            self.compute_sinad()

        epsilon = 1e-12
        signal_db = 10 * np.log10(self.signal_power + epsilon)  # 신호 전력 dB 계산
        noise_db = 10 * np.log10(self.noise_power + epsilon)    # 노이즈 전력 dB 계산

        # 바 그래프 항목과 값 설정
        labels = ["Signal Power (dB)", "Noise Power (dB)", "SNR (dB)", "SINAD (dB)"]
        values = [signal_db, noise_db, self.snr_db, self.sinad_db]

        # 그래프 출력
        plt.figure(figsize=(8, 6))
        plt.bar(labels, values, color=["blue", "red", "green", "purple"])
        plt.ylabel("Power (dB)")
        plt.title("Noise, Signal, SNR, and SINAD Comparison (in dB)")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def evaluate_audio_quality(self, snr_threshold=30):
        snr = self.compute_snr()
        sinad = self.compute_sinad()

        print("\n--- 신호 품질 평가 결과 ---")
        print(f"🔹 계산된 SNR: {snr:.2f} dB")
        print(f"🔹 계산된 SINAD: {sinad:.2f} dB")

        # 임계값과 비교해 품질 판정
        if snr >= snr_threshold:
            print("\n✅ 결과: PASS (신호 품질 양호)")
        else:
            print("\n❌ 결과: FAIL (노이즈 많음)")

        # 그래프 표시
        self.plot_noise_sinad()

    def analyze_silence(self, rms_threshold=100, spike_threshold=5000, show_log=True):
        if self.data is None:
            self.load_wave()

        data = self.data

        # 1. DC 오프셋 확인
        mean_val = np.mean(data)

        # 2. RMS 값 계산
        rms_val = np.sqrt(np.mean(data ** 2))

        # 3. Peak 진폭 확인
        peak_val = np.max(np.abs(data))

        # 4. 무음 여부 판단
        is_silent = rms_val < rms_threshold and peak_val < spike_threshold and abs(mean_val) < rms_threshold

        if show_log:
            print("\n--- 무음 분석 결과 ---")
            print(f"평균값 (DC 오프셋): {mean_val:.2f}")
            print(f"RMS 값: {rms_val:.2f}")
            print(f"최대 진폭: {peak_val:.2f}")
            if is_silent:
                print("✅ 결과: 실제 무음 상태로 판단됩니다.")
            else:
                print("❌ 결과: 무음이 아닌 신호 또는 이상 데이터가 포함되어 있습니다.")

        return is_silent