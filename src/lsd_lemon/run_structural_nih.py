#from structural_cbstools import create_structural
from structural import create_structural
import sys

'''
Meta script to run structural preprocessing
------------------------------------------
Can run in two modes:
python run_structural.py s {subject_id} {anat_path} {anat_prefix}
python run_structural.py f {text file containing list of subjects} {anat_path} {anat_prefix}
'''

mode=sys.argv[1]

anat_path=sys.argv[3]
anat_prefix=sys.argv[4]

if mode == 's':
    subjects=[sys.argv[2]]
elif mode == 'f':
    with open(sys.argv[2], 'r') as f:
        subjects = [line.strip() for line in f]

for subject in subjects:
    
    print 'Running subject '+subject
    
    working_dir =    '/data/SFIMJGC_Introspec/pdn/WorkDir/'+subject+'/'            # '/scr/ilz2/LEMON_LSD/working_dir_struct/' +subject+'/' 
    data_dir =       anat_path                                                                 # '/scr/ilz2/LEMON_LSD/'+subject+'/'
    out_dir =        '/data/SFIMJGC_Introspec/pdn/PrcsData/'+subject+'/'          #'/scr/ilz2/LEMON_LSD/'+subject+'/'
    freesurfer_dir = '/data/SFIMJGC_Introspec/pdn/Freesurfer'                     # '/scr/ilz2/LEMON_LSD/freesurfer/'
    standard_brain = '/usr/local/apps/fsl/5.0.10/data/standard/MNI152_T1_1mm_brain.nii.gz'   #'/usr/share/fsl/5.0/data/standard/MNI152_T1_1mm_brain.nii.gz'
    
    create_structural(subject=subject, working_dir=working_dir, data_dir=data_dir, 
                freesurfer_dir=freesurfer_dir, out_dir=out_dir,
                standard_brain=standard_brain, anat_prefix=anat_prefix)
    
