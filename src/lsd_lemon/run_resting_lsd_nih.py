from lsd_resting_nih import create_lsd_resting_nih
import sys

'''
Meta script to run lsd resting state preprocessing
-------------------------------------------------
Can run in two modes:
python run_lsd_resting.py s {subject_id}
python run_lsd_resting.py f {text file containing list of subjects}
'''

mode=sys.argv[1]

if mode == 's':
    subjects=[sys.argv[2]]
elif mode == 'f':
    with open(sys.argv[2], 'r') as f:
        subjects = [line.strip() for line in f]

for subject in subjects:
    
    print 'Running subject '+subject

    working_dir =     '/data/SFIMJGC_Introspec/pdn/WorkDir/'+subject+'/'   #'/scr/ilz2/LEMON_LSD/working_dir_lsd/'+subject+'/' 
    lsd_dir =         '/data/SFIMJGC_Introspec/pdn/PrcsData/'+subject+'/'        #'/scr/ilz2/LEMON_LSD/'+subject+'/'             
    freesurfer_dir =  '/data/SFIMJGC_Introspec/pdn/Freesurfer'          #'/scr/ilz2/LEMON_LSD/freesurfer/'
    #data_dir =        '/data/SFIMJGC_Introspec/lsd_dataset/rawdata/'+subject+'/'   #'/scr/ilz2/LEMON_LSD/'+subject+'/preprocessed/lsd_resting/'
    data_dir =        '/data/DSST/MPI_LEMON/ds000221-download/'+subject+'/'   #'/scr/ilz2/LEMON_LSD/'+subject+'/preprocessed/lsd_resting/'
    echo_space       = 0.00067 #in sec
    te_diff          = 2.46 #in ms
    epi_resolution   = 2.3
    TR=1.4
    highpass=0.01
    lowpass=0.1
    vol_to_remove = 5
    scans=['ses-02_task-rest_acq-AP_run-01_bold',
           'ses-02_task-rest_acq-AP_run-02_bold',
           'ses-02_task-rest_acq-PA_run-01_bold',
           'ses-02_task-rest_acq-PA_run-02_bold']


    create_lsd_resting_nih(subject=subject, working_dir=working_dir, out_dir=lsd_dir, 
                    freesurfer_dir=freesurfer_dir, data_dir=data_dir, 
                    echo_space=echo_space, te_diff=te_diff, scans=scans,
                    vol_to_remove=vol_to_remove, epi_resolution=epi_resolution,
                    TR=TR, highpass=highpass, lowpass=lowpass)
