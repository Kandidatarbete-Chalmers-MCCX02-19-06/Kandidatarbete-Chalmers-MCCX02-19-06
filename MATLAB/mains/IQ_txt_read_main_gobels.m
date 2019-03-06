addpath(genpath(pwd))
addpath('Dataread')
addpath('tracker')
clc
clear all
format shorteng
%addpath("IQ Read")
%addpath("Target tracking")

filename = 'Manniska_Sweep100_0227_Test1.csv'%kort fil
%filename = 'Manniska_1_Sweep100.csv'%lång fil?

[dist,amp, phase,t,gain, L_start, L_end, L_data, L_seq, Fs] = IQ_read_3(filename);
gain = gain
L_start = L_start
L_end = L_end
L_data = L_data
L_seq = L_seq
Fs = Fs
c = 3e8;%[m/s] 
fc = 60.5e9;% [Hz]
wavelength = c/fc

%test of matched filter
MF = amp(1,:).*(cos(phase(1,:)) + 1i*sin(phase(1,:)) );%get the first vector for matched filter
MF = flip(MF);
Emf = sum(abs(MF).^2);
%conv(data,filter,SHAPE,'same');

for i = 1:L_seq
    filtered_refl(i,:) = filter(MF,Emf, (amp(i,:).*(cos(phase(i,:)) + 1i*sin(phase(i,:)) ) ));
    i = i + 1;
end

%amp = abs(filtered_refl);
%phase = angle(filtered_refl);

[T,D,A,P] = SURF_PREP(dist,amp, phase,t);


%Detektering och följning utav mål
start_distance = 0.37%m
N_avg = 10;
[t,target_amplitude, target_phase, target_distance] = target_tracker_2(t,dist,amp,phase,start_distance,N_avg);

figure(1)
subplot(1,2,1)
plot(dist,amp(1,:))
ylabel('Amplitude []')
xlabel('Distance [m]')


subplot(1,2,2)
plot(dist,phase(1,:))
ylabel('phase []')
xlabel('Distance [m]')

%surf test
figure(2)
surf(T,D,A)
ylabel('Distance [m]')
xlabel('Time [s]')
zlabel('Reflection amplitude')

figure(3)
surf(T,D,P)
ylabel('Distance [m]')
xlabel('Time [s]')
zlabel('Reflection phase [rad]')


%unwrap test
target_phase = unwrap(target_phase);


%Signal filtreringstest
disp('Downsampling with ratio r:')
r = 6
%Down sampling
target_amplitude = decimate(target_amplitude,r);
target_phase = decimate(target_phase,r);
target_distance = decimate(target_distance,r);
t = decimate(t,r);
L_seq = L_seq/r%new length in time domain
Fs = Fs/r%New sample rate in time domain


%Delta distance of tracked target
target_delta_distance = wavelength/2/pi/2*target_phase;

%filer data into two bandwidths
F_low_BR = 0.15
F_high_BR = 0.8

F_low_HR = 0.85
F_high_HR = 6
BWrel_transband_BR = 0.5
BWrel_transband_HR = 0.2
Atten_stopband = 40
[delta_distance_BR] = bandpassfilter(target_delta_distance,Fs,F_low_BR,F_high_BR,BWrel_transband_BR,Atten_stopband);
[delta_distance_HR] = bandpassfilter(target_delta_distance,Fs,F_low_HR,F_high_HR,BWrel_transband_HR,Atten_stopband);

%FFTs
F_resolution = 0.01 %[Hz]
[f_BR,delta_distance_BR] = smartFFT_abs(delta_distance_BR,Fs,F_resolution);
[f_HR,delta_distance_HR] = smartFFT_abs(delta_distance_HR,Fs,F_resolution);

%Frequency finding
BW_comb = 0.05 %[Hz] Tightness of tone scanning
%Scan span for breating rate
%Fscan_lower_BR = F_low_BR
%Fscan_upper_BR = F_low_BR/3

%Scan span for heartrate
Fscan_lower_HR = F_low_HR
Fscan_upper_HR = F_high_HR/4
%f_detected_BR = basetone_finder(f_BR,delta_distance_BR,Fs,F_low_BR,F_high_BR,BW_comb)
f_detected_HR = basetone_finder(f_HR,delta_distance_HR,Fs,F_low_HR,F_high_HR,BW_comb)
BPM_HR = 60*f_detected_HR

%Plots
figure(5)
subplot(1,2,1)
plot(f_BR,delta_distance_BR)
ylabel('FFT of BR spectrum')
xlabel('f [Hz]')
xlim([F_low_BR F_high_BR])

subplot(1,2,2)
plot(f_HR,delta_distance_HR)
ylabel('FFT of HR spectrum')
xlabel('f [Hz]')
xlim([F_low_HR F_high_HR])


figure(6)
subplot(2,2,1)
plot(t,target_amplitude)
xlabel('t [s]')
ylabel('Amplitude of tracked target [arb]')

subplot(2,2,2)
plot(t,target_phase)
xlabel('t [s]')
ylabel('Phase of tracked target [rad]')

subplot(2,2,3)
plot(t,target_distance)
xlabel('t [s]')
ylabel('Distance of tracked target [m]')

subplot(2,2,4)
plot(t,5e-3/2/pi/2*(target_phase - mean(target_phase)))
xlabel('t [s]')
ylabel('Delta distance of tracked target [m]')






