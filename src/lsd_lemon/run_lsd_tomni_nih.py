from lsd_tomni_nih import create_lsd_tomni_nih
import sys




'''
Meta script to run lsd transformation into MNI
----------------------------------------------
python run_lsd_resting.py s {subject_id}
'''

mode=sys.argv[1]

if mode == 's':
    subject=sys.argv[2]


print 'Running subject: '+subject

data_dir = '/data/SFIMJGC_Introspec/pdn/PrcsData/'+subject+'/'
base_dir = '/data/SFIMJGC_Introspec/pdn/WorkDir/'+subject+'/'
out_dir  = '/data/SFIMJGC_Introspec/pdn/PrcsData/'+subject+'/'

template ='/usr/local/apps/fsl/5.0.10/data/standard/MNI152_T1_2mm_brain.nii.gz'

scans   = ['ses-02_task-rest_acq-AP_run-01_bold',
           'ses-02_task-rest_acq-AP_run-02_bold',
           'ses-02_task-rest_acq-PA_run-01_bold',
           'ses-02_task-rest_acq-PA_run-02_bold']

create_lsd_tomni_nih(subject=subject,
                     data_dir=data_dir,
                     base_dir=base_dir,
                     out_dir=out_dir, 
                     scans=scans,
                     template=template)
