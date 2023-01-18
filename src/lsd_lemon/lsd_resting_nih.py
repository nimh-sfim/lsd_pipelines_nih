from nipype.pipeline.engine import Node, Workflow, JoinNode
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
from func_preproc.strip_rois import strip_rois_func
from func_preproc.moco import create_moco_pipeline
from func_preproc.fieldmap_coreg import create_fmap_coreg_pipeline
from func_preproc.transform_timeseries import create_transform_pipeline
from func_preproc.denoise import create_denoise_pipeline

'''
Main workflow for lsd resting state preprocessing.
===================================================
Uses file structure set up by conversion script.

Equivalent to lemon resting but iterating over all 4 scans with their
respective files and parameters for distortion correction.
'''


def create_lsd_resting_nih(subject, working_dir, out_dir, freesurfer_dir, data_dir, 
                    echo_space, te_diff, vol_to_remove, scans, epi_resolution,
                    TR, highpass, lowpass):

   #main workflow
   func_preproc          = Workflow(name='lsd_resting_nih')
   func_preproc.base_dir = working_dir
   func_preproc.config['execution']['crashdump_dir'] = func_preproc.base_dir + "/crash_files"
   func_preproc.config['execution']['remove_node_directories'] = True
   func_preproc.config['execution']['remove_unnecessary_outputs'] = True
   
   # set fsl output type to nii.gz
   fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
   
   # infosource to iterate over scans
   scan_infosource = Node(util.IdentityInterface(fields=['scan_id']),name='scan_infosource')
   scan_infosource.iterables=('scan_id', scans)
   
   # select files... goes from scan_id and fmap_id to the actual location of the input files
   # =======================================================================================
   templates={'func':       data_dir+'/ses-02/func/'+subject+'_{scan_id}.nii.gz',
              'fmap_phase': data_dir+'/ses-02/fmap/'+subject+'_{fmap_id}_phasediff.nii.gz',
              'fmap_mag':   data_dir+'/ses-02/fmap/'+subject+'_{fmap_id}_magnitude2.nii.gz',
              'anat_head':  out_dir + 'preprocessed/anat/T1.nii.gz',
              'anat_brain': out_dir + 'preprocessed/anat/T1_brain.nii.gz',
              'func_mask':  out_dir + 'preprocessed/anat/func_mask.nii.gz',}
   selectfiles = Node(nio.SelectFiles(templates, base_directory=data_dir), name="selectfiles")
   
   # Remove initial 5 volumes from the different resting-state runs
   # ==============================================================
   remove_vol = Node(util.Function(input_names=['in_file','t_min'], output_names=["out_file"],function=strip_rois_func),name='remove_vol')
   remove_vol.inputs.t_min = vol_to_remove
   
   # function node to get fieldmap information
   # =========================================
   def fmap_info(scan_id):
       if scan_id=='ses-02_task-rest_acq-AP_run-01_bold':
           fmap_id='ses-02_acq-GEfmap_run-01'
           pe_dir='y-' #Original Configuration (correct)
       elif scan_id=='ses-02_task-rest_acq-PA_run-01_bold':
           fmap_id='ses-02_acq-GEfmap_run-01'
           pe_dir='y'  #Original Configuration
       elif scan_id=='ses-02_task-rest_acq-AP_run-02_bold':
           fmap_id='ses-02_acq-GEfmap_run-02'
           pe_dir='y-' #Original Configuration
       elif scan_id=='ses-02_task-rest_acq-PA_run-02_bold':
           fmap_id='ses-02_acq-GEfmap_run-02'
           pe_dir='y' #Original Configuration 
       return fmap_id, pe_dir
   
   fmap_infosource=Node(util.Function(input_names=['scan_id'], output_names=['fmap_id', 'pe_dir'], function=fmap_info),name='fmap_infosource')
   
   # workflow for motion correction
   # ==============================
   moco=create_moco_pipeline()
   
   # workflow for fieldmap correction and coregistration
   # ===================================================
   # This will compute all necessary transformations, but will not apply them
   fmap_coreg=create_fmap_coreg_pipeline()
   fmap_coreg.inputs.inputnode.fs_subjects_dir=freesurfer_dir
   fmap_coreg.inputs.inputnode.fs_subject_id=subject
   fmap_coreg.inputs.inputnode.echo_space=echo_space
   fmap_coreg.inputs.inputnode.te_diff=te_diff
   
   # workflow for applying transformations to timeseries
   # ===================================================
   # Generate ts dataset following:
   # 1) Removal of initial 5 volumes
   # 2) Motion correction
   # 3) Distortion correction using field map
   transform_ts = create_transform_pipeline()
   transform_ts.inputs.inputnode.resolution=epi_resolution
   
   # workflow to denoise timeseries
   denoise = create_denoise_pipeline()
   denoise.inputs.inputnode.highpass_sigma= 1./(2*TR*highpass)
   denoise.inputs.inputnode.lowpass_sigma= 1./(2*TR*lowpass)
   # https://www.jiscmail.ac.uk/cgi-bin/webadmin?A2=ind1205&L=FSL&P=R57592&1=FSL&9=A&I=-3&J=on&d=No+Match%3BMatch%3BMatches&z=4 
   denoise.inputs.inputnode.tr = TR
   
   # Move important outputs to the PrcsData folder within prcs_data_nipype
   # =====================================================================
   sink = Node(nio.DataSink(parameterization=True,base_directory=out_dir,
                            substitutions=[('rest_realigned.nii.gz_abs.rms', 'rest_realigned_abs.rms'),
                                               ('rest_realigned.nii.gz.par','rest_realigned.par'),
                                               ('rest_realigned.nii.gz_rel.rms', 'rest_realigned_rel.rms'),
                                               ('rest_realigned.nii.gz_abs_disp', 'abs_displacement_plot'),
                                               ('rest_realigned.nii.gz_rel_disp', 'rel_displacment_plot'),
                                               ('rest2anat_denoised.nii.gz','rest_denoised.nii.gz')])
                           ,name='sink')
   ## OCTOBER 27th 2021
   ## ORIGINAL WORKFLOW GENERATED BY JAVIER: Sink node writes many files to PrcsData folder
   ## To minimize the footprint of the workflow the version below (uncommented) is an equivalent
   ## to the one here but with only the minimum number of files being writen out to the sink node   
   ## func_preproc.connect([(scan_infosource, selectfiles, [('scan_id','scan_id')]),
   ##                       (scan_infosource, fmap_infosource, [('scan_id', 'scan_id')]),
   ##                       (fmap_infosource, selectfiles, [('fmap_id', 'fmap_id')]),
   ##                       (fmap_infosource, fmap_coreg, [('pe_dir', 'inputnode.pe_dir')]),
   ##                       (selectfiles, remove_vol, [('func','in_file')]),
   ##                       (remove_vol, moco, [('out_file', 'inputnode.epi')]),
   ##                       (remove_vol, sink, [('out_file','pb00_discard')]),
   ##                       (moco, sink, [('outputnode.epi_moco',  'pb01_moco.@realigned_ts'),
   ##                                     ('outputnode.par_moco',  'pb01_moco.@par'),
   ##                                     ('outputnode.rms_moco',  'pb01_moco.@rms'),
   ##                                     ('outputnode.epi_mean',  'pb01_moco.@mean'),
   ##                                     ('outputnode.rotplot',   'pb01_moco.plots.@rotplot'),
   ##                                     ('outputnode.transplot', 'pb01_moco.plots.@transplot'),
   ##                                     ('outputnode.dispplots', 'pb01_moco.plots.@dispplots'),
   ##                                     ('outputnode.tsnr_file', 'pb01_moco.@tsnr')]),
   ##                       (selectfiles, fmap_coreg, [('fmap_phase', 'inputnode.phase'),
   ##                                                      ('fmap_mag', 'inputnode.mag'),
   ##                                                      ('anat_head', 'inputnode.anat_head'),
   ##                                                      ('anat_brain', 'inputnode.anat_brain')
   ##                                                      ]),
   ##                       (moco, fmap_coreg, [('outputnode.epi_mean', 'inputnode.epi_mean')]),
   ##                       (fmap_coreg, sink, [('outputnode.fmap','pb02_fmap.transforms2anat.@fmap'),
   ##                                               ('outputnode.unwarpfield_epi2fmap',   'pb02_fmap.@unwarpfield_epi2fmap'),
   ##                                               ('outputnode.unwarped_mean_epi2fmap', 'pb02_fmap.@unwarped_mean_epi2fmap'),
   ##                                               ('outputnode.epi2fmap',               'pb02_fmap.@epi2fmap'),
   ##                                               ('outputnode.shiftmap',               'pb02_fmap.@shiftmap'),
   ##                                               ('outputnode.fmap_fullwarp',          'pb02_fmap.transforms2anat.@fmap_fullwarp'),
   ##                                               ('outputnode.epi2anat',               'pb02_fmap.@epi2anat'),
   ##                                               ('outputnode.epi2anat_mat',           'pb02_fmap.transforms2anat.@epi2anat_mat'),
   ##                                               ('outputnode.epi2anat_dat',           'pb02_fmap.transforms2anat.@epi2anat_dat'),
   ##                                               ('outputnode.epi2anat_mincost',       'pb02_fmap.@epi2anat_mincost')
   ##                                               ]),
   ##                       (remove_vol, transform_ts, [('out_file', 'inputnode.orig_ts')]),
   ##                       (selectfiles, transform_ts, [('anat_head', 'inputnode.anat_head')]),
   ##                       (moco, transform_ts, [('outputnode.mat_moco', 'inputnode.mat_moco')]),
   ##                       (fmap_coreg, transform_ts, [('outputnode.fmap_fullwarp', 'inputnode.fullwarp')]),
   ##                       (transform_ts, sink, [('outputnode.trans_ts',      'pb03_coregister.@full_transform_ts'),
   ##                                             ('outputnode.trans_ts_mean', 'pb03_coregister.@full_transform_mean'),
   ##                                             ('outputnode.resamp_brain',  'pb03_coregister.@resamp_brain')]),
   ##                       (selectfiles, denoise,  [('func_mask',                         'inputnode.brain_mask'),
   ##                                                ('anat_brain',                        'inputnode.anat_brain')]),
   ##                       (fmap_coreg, denoise,   [('outputnode.epi2anat_dat',           'inputnode.epi2anat_dat'),
   ##                                                ('outputnode.unwarped_mean_epi2fmap', 'inputnode.unwarped_mean')]),
   ##                       (moco, denoise,         [('outputnode.par_moco',               'inputnode.moco_par')]),
   ##                       (transform_ts, denoise, [('outputnode.trans_ts',               'inputnode.epi_coreg')]),
   ##                       (denoise, sink, [('outputnode.wmcsf_mask',        'pb04_denoise.mask.@wmcsf_masks'),
   ##                                        ('outputnode.combined_motion',   'pb04_denoise.artefact.@combined_motion'),
   ##                                        ('outputnode.outlier_files',     'pb04_denoise.artefact.@outlier'),
   ##                                        ('outputnode.intensity_files',   'pb04_denoise.artefact.@intensity'),
   ##                                        ('outputnode.outlier_stats',     'pb04_denoise.artefact.@outlierstats'),
   ##                                        ('outputnode.outlier_plots',     'pb04_denoise.artefact.@outlierplots'),
   ##                                        ('outputnode.mc_regressor',      'pb04_denoise.regress.@mc_regressor'),
   ##                                        ('outputnode.comp_regressor',    'pb04_denoise.regress.@comp_regressor'),
   ##                                        ('outputnode.mc_F',              'pb04_denoise.regress.@mc_F'),
   ##                                        ('outputnode.mc_pF',             'pb04_denoise.regress.@mc_pF'),
   ##                                        ('outputnode.comp_F',            'pb04_denoise.regress.@comp_F'),
   ##                                        ('outputnode.comp_pF',           'pb04_denoise.regress.@comp_pF'),
   ##                                        ('outputnode.brain_mask_resamp', 'pb04_denoise.mask.@brain_resamp'),
   ##                                        ('outputnode.brain_mask2epi',    'pb04_denoise.mask.@brain_mask2epi'),
   ##                                        ('outputnode.normalized_file',   '@normalized')])
   ##                      ])
   
   func_preproc.connect([(scan_infosource, selectfiles, [('scan_id','scan_id')]),
                         (scan_infosource, fmap_infosource, [('scan_id', 'scan_id')]),
                         (fmap_infosource, selectfiles, [('fmap_id', 'fmap_id')]),
                         (fmap_infosource, fmap_coreg, [('pe_dir', 'inputnode.pe_dir')]),
                         (selectfiles, remove_vol, [('func','in_file')]),
                         (remove_vol, moco, [('out_file', 'inputnode.epi')]),
                         (moco, sink, [('outputnode.epi_moco',  'preprocessed.func.pb01_moco.@realigned_ts'),
                                       ('outputnode.par_moco',  'preprocessed.func.pb01_moco.@par'),
                                       ('outputnode.rms_moco',  'preprocessed.func.pb01_moco.@rms'),
                                       ('outputnode.epi_mean',  'preprocessed.func.pb01_moco.@mean'),
                                       ('outputnode.rotplot',   'preprocessed.func.pb01_moco.plots.@rotplot'),
                                       ('outputnode.transplot', 'preprocessed.func.pb01_moco.plots.@transplot'),
                                       ('outputnode.dispplots', 'preprocessed.func.pb01_moco.plots.@dispplots'),
                                       ('outputnode.tsnr_file', 'preprocessed.func.pb01_moco.@tsnr')]),
                         (selectfiles, fmap_coreg, [('fmap_phase', 'inputnode.phase'),
                                                        ('fmap_mag', 'inputnode.mag'),
                                                        ('anat_head', 'inputnode.anat_head'),
                                                        ('anat_brain', 'inputnode.anat_brain')
                                                        ]),
                         (moco, fmap_coreg, [('outputnode.epi_mean', 'inputnode.epi_mean')]),
                         (fmap_coreg, sink, [('outputnode.epi2anat',               'preprocessed.func.pb02_fmap.@epi2anat'),
                                             ('outputnode.epi2anat_mat',           'preprocessed.func.pb02_fmap.transforms2anat.@epi2anat_mat'),
                                             ('outputnode.epi2anat_dat',           'preprocessed.func.pb02_fmap.transforms2anat.@epi2anat_dat')]),
                         (remove_vol, transform_ts, [('out_file', 'inputnode.orig_ts')]),
                         (selectfiles, transform_ts, [('anat_head', 'inputnode.anat_head')]),
                         (moco, transform_ts, [('outputnode.mat_moco', 'inputnode.mat_moco')]),
                         (fmap_coreg, transform_ts, [('outputnode.fmap_fullwarp', 'inputnode.fullwarp')]),
                         (selectfiles, denoise,  [('func_mask',                         'inputnode.brain_mask'),
                                                  ('anat_brain',                        'inputnode.anat_brain')]),
                         (fmap_coreg, denoise,   [('outputnode.epi2anat_dat',           'inputnode.epi2anat_dat'),
                                                  ('outputnode.unwarped_mean_epi2fmap', 'inputnode.unwarped_mean')]),
                         (moco, denoise,         [('outputnode.par_moco',               'inputnode.moco_par')]),
                         (transform_ts, denoise, [('outputnode.trans_ts',               'inputnode.epi_coreg')]),
                         (transform_ts, sink, [('outputnode.trans_ts',      'preprocessed.func.pb03_coregister.@full_transform_ts'),
                                               ('outputnode.trans_ts_mean', 'preprocessed.func.pb03_coregister.@full_transform_mean'),
                                               ('outputnode.resamp_brain',  'preprocessed.func.pb03_coregister.@resamp_brain')]),
                         (denoise, sink, [('outputnode.wmcsf_mask',        'preprocessed.func.pb04_denoise.mask.@wmcsf_masks'),
                                          ('outputnode.combined_motion',   'preprocessed.func.pb04_denoise.artefact.@combined_motion'),
                                          ('outputnode.outlier_files',     'preprocessed.func.pb04_denoise.artefact.@outlier'),
                                          ('outputnode.intensity_files',   'preprocessed.func.pb04_denoise.artefact.@intensity'),
                                          ('outputnode.outlier_stats',     'preprocessed.func.pb04_denoise.artefact.@outlierstats'),
                                          ('outputnode.outlier_plots',     'preprocessed.func.pb04_denoise.artefact.@outlierplots'),
                                          ('outputnode.mc_regressor',      'preprocessed.func.pb04_denoise.regress.@mc_regressor'),
                                          ('outputnode.comp_regressor',    'preprocessed.func.pb04_denoise.regress.@comp_regressor'),
                                          ('outputnode.mc_F',              'preprocessed.func.pb04_denoise.regress.@mc_F'),
                                          ('outputnode.mc_pF',             'preprocessed.func.pb04_denoise.regress.@mc_pF'),
                                          ('outputnode.comp_F',            'preprocessed.func.pb04_denoise.regress.@comp_F'),
                                          ('outputnode.comp_pF',           'preprocessed.func.pb04_denoise.regress.@comp_pF'),
                                          ('outputnode.brain_mask_resamp', 'preprocessed.func.pb04_denoise.mask.@brain_resamp'),
                                          ('outputnode.brain_mask2epi',    'preprocessed.func.pb04_denoise.mask.@brain_mask2epi'),
                                          ('outputnode.normalized_file',   'preprocessed.func.pb04_denoise.data.@normalized'),
                                          ('outputnode.bandpassed_file',   'preprocessed.func.pb04_denoise.data.@bandpassed'),
                                          ('outputnode.denoised_file',     'preprocessed.func.pb04_denoise.data.@denoised')])  ])
   
   func_preproc.write_graph(dotfilename='func_preproc.dot', graph2use='flat', format='pdf', simple_form=False)
   
   func_preproc.run()
