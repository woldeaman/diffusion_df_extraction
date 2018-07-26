% exemplary script showing pre-processing steps of microscopy data
clear;

data_path='/Users/woldeaman/Downloads/180724-ah202-g6-d70_forts/'; % supply path to data
filename='180724-ah202.lif_180724-ah202-g6-d70 forts';  % supply filenames here
z_max=44;  % number of recorde z-stacks
t_max=57;  % number of recorded time points

int=[];

for it=0:t_max
    % set up correct image names for each time point and z-position
    file_ext_t=num2str(it);
    while length(file_ext_t)<length(num2str(t_max))
        file_ext_t=strcat('0',file_ext_t);
    end
    file_ext_t=strcat('_t',file_ext_t);
    base_str_out=strcat(filename,file_ext_t,'.tif');

    int_tmp=[];
    int_tmp_ref=[];

    for iz=0:z_max
        file_ext_z=num2str(iz);
        while length(file_ext_z)<length(num2str(z_max))
            file_ext_z=strcat('0',file_ext_z);
        end
        file_ext_z=strcat('_z',file_ext_z,'_ch00.tif');
        base_str_in=strcat(filename,file_ext_t,file_ext_z);

        tmp=double(imread(strcat(data_path,base_str_in),1));
        % NOTE: this is an edge correction,
        % if activated discarding values at the image boundaries
%         tmp=tmp(10:end-10,10:end-10);
        int_tmp=[int_tmp; mean(mean(tmp))];
    end

    % NOTE: this is a baseline correction,
    % intensity in glass should be zero, substract any non zero contributions
   int_tmp=int_tmp-mean(int_tmp(1:7));
   % pp=polyfit((length(int_tmp)-12:length(int_tmp)),int_tmp(end-12:end)',1);
   % int_tmp=int_tmp./polyval(pp,(1:length(int_tmp)))';
   % NOTE: this is the normalization,
   % intensity increases over time, thats why we normalize to bulk value
   %int_tmp=int_tmp./mean(int_tmp(38:45));

    int=[int int_tmp];

%     if iF==1
%         figure
%         plot(int_tmp,'.')
%         hold on
%     else
%         plot(int_tmp,'.')
%     end
end