%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% Author: Aron Glennon
% Date: 9/18/2008
% 
% Constraints:
%   This handles mono files only
% 
% Assumptions:
%   I assume the user will enter appropriate values for each parameter
%   (i.e. there is no error checking)
%
% Function Signature:
% [X,Y,Z] = fftCompare(wavFile, windowSampleCount, hopFactor, windowType)
%
% Inputs:
% --wavfile - The location of a .wav file
% --windowSampleCount - The length of the desired window in samples
% --hopFactor - The hop factor associated with the desired window length.
%   A hopfactor of 2 means 50% overlap, 4 means 75%, etc.
% --windowType - use 1 for Rectangular, 2 for Hanning, and 3 for Blackman
%
% Outputs:
% --X - Output using fft loop method
% --Y - Output using Matlab's spectrogram function
% --Z - Outputs the difference (via subtraction) between X and Y.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [fftMethodAmps, specMethodAmps, diffMatrix] = fftCompare(wavFile, windowSampleCount, hopFactor, windowType)

    % Get .wav data into Matlab
	[input, sr, bits] = wavread(wavFile);
    
    % Calc the number of samples to hop after each analysis frame.
	hopSampleCount = floor(windowSampleCount/hopFactor); 

    % Calc the total number of frames given the input length
	frameCount = floor(length(input) / hopSampleCount);
    
    % Pad the input with zeros to protect from overshooting last window.
    input = [input; zeros(windowSampleCount,1)];
    
    % Create 'windowFunction' using the 'windowType' input.
    if windowType == 1
        
		windowFunction = ones(windowSampleCount,1);			% Rectangular
	
	elseif windowType == 2
		
		windowFunction = hanning(windowSampleCount);		% Hanning
	
	elseif windowType == 3
		
		windowFunction = blackman(windowSampleCount);		% Blackman
    end % end if statement

    % The following initializes fftMethodAmps values to zero
    fftMethodAmps = zeros(windowSampleCount, frameCount); 
    for i = 0:(frameCount-1)	
        currentWindowSamples = input((i*hopSampleCount + 1) : (i*hopSampleCount + windowSampleCount)) .* windowFunction;  
	
        % We then perform an fft on currentWindowSamples and set the result 
        % to currentFreqVals.
    	currentFreqVals = fft(currentWindowSamples);
	
        % I have chosen to normalize the FFT below to 0.5 to preserve the 
        % conservation of energy (i.e. since our input time-domain waveform
        % is composed of simple sines with amplitude between 0 and 1, we 
        % must ensure that the amplitudes of the frequency data do not 
        % extend past 1.  At first glance one may decide to normalize the 
        % frequency data to 1, but on further inspection 0.5 becomes the 
        % clear choice due to the symmetric frequency components about the 
        % Nyquist frequency.
        magnitude = abs(currentFreqVals) .* (1/length(currentWindowSamples));
		
        % Normalized amplitude values are then mapped to decibels
        magnitude = 20 .* log10(magnitude);

        % The data in the magnitude vector is then written to the 
        % appropriate frame (column) in the fftMethodAmps matrix
    	fftMethodAmps(:,i+1) = magnitude;

    end %end for loop

    %Eliminate redundant freq data for comparison
    fftMethodAmps = fftMethodAmps((ceil(1:end/2)), :);
    % Use Matlab's spectrogram function to calculate STFT
    specMethodAmps = spectrogram(input, windowFunction, (windowSampleCount - hopSampleCount));
    
    % Find the normalized magnitudes of the rectilinear complex numbers 
    % returned by the spectrogram function.
    specMethodAmps = abs(specMethodAmps) ./ length(currentWindowSamples);
    specMethodAmps = 20 .* log10(specMethodAmps);
    % Plot the functions (I stripped off the last row and column of the
    % specMethodAmps matrix so that the plots had the same dimension and
    % therefore could be better compared visually).
    
    for i = 0:(frameCount-1)
        time(i+1) = windowSampleCount/sr*i;
    end
    for i = 0:(windowSampleCount/2-1)
        freqs(i+1) = sr/windowSampleCount*i;
    end
    imagesc([0; (frameCount-1)*windowSampleCount/sr/hopFactor], [0; sr/2], specMethodAmps(1:end-1, 1:end-1));
            title('STFT');
            xlabel('Time (s)');
            ylabel('Frequency (Hz)');
            colorbar;
            set(gca,'YDir','normal');
            yt = get(gca,'YTick');
            set(gca,'YTickLabel', sprintf('%d|',yt))
%     subplot(2, 1, 1);
%         imagesc(fftMethodAmps);
%             title('FFT Loop Method');
%             xlabel('Frame Number');
%             ylabel('Frequency Bin');
%             colorbar;
%     subplot(2, 1, 2);
        
            
    % Find difference between the two sets of data (again note that I have 
    % stripped off the last row and column of specMethodAmps in
    % order to perform matrix subtraction, since this operation requires
    % that both matrices have the same dimensions).
    %diffMatrix = fftMethodAmps-specMethodAmps(1:end-1, 1:end-1);
    %if diffMatrix == zeros(size(diffMatrix))
    %    fprintf('The two plots are identical\n');
    %else
    %    fprintf('The two plots are not identical.  Please look at diffMatrix to see how they differ\n');
    %end %end if statement
            
end %end function