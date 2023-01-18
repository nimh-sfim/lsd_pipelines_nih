import nipype.interfaces.fsl as fsl
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.ants as ants
from nipype.pipeline.engine import Node, Workflow

'''
Project preprocessed lemon resting state from 
individual structural to MNI152 2mm space
'''
def create_lsd_tomni_nih(subject, data_dir, base_dir,out_dir, scans, template):

    # Main Workflow
    # =============
    mni          = Workflow(name='mni')
    mni.base_dir = base_dir
    mni.config['execution']['crashdump_dir'] = mni.base_dir + "/crash_files"
    
    # set fsl output type to nii.gz
    # =============================
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    
    # NODE 0. infosource for subjects
    # ===============================
    subject_infosource=Node(util.IdentityInterface(fields=['subject_id']), name='subject_infosource')
    subject_infosource.iterables=('subject_id', [subject])
    
    # NODE 1. infosource to iterate over scans
    # ========================================
    scan_infosource = Node(util.IdentityInterface(fields=['scan_id']),name='scan_infosource')
    scan_infosource.iterables=('scan_id', scans)
    
    # NODE 2. select files... goes from scan_id and fmap_id to the actual location of the input files
    # ===============================================================================================
    templates = {'rest_dbn':   data_dir+'/preprocessed/func/pb04_denoise/data/_scan_id_{scan_id}'+'/rest_denoised_bandpassed_norm.nii.gz',
                 'rest_db':   data_dir+'/preprocessed/func/pb04_denoise/data/_scan_id_{scan_id}'+'/rest_denoised_bandpassed.nii.gz',
                 'rest_d':   data_dir+'/preprocessed/func/pb04_denoise/data/_scan_id_{scan_id}'+'/rest_denoised.nii.gz',
                 'gm':       data_dir+'/preprocessed/anat/gm.nii.gz',
                 'affine': data_dir+'/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
                 'warp':   data_dir+'/preprocessed/anat/transforms2mni/transform1Warp.nii.gz'}
    
    selectfiles = Node(nio.SelectFiles(templates, base_directory=data_dir), name="selectfiles")
    
    # NODE 3. make filelist
    # =====================
    translist = Node(util.Merge(2), name='translist')
    
    # NODE 4. apply all transforms
    # ============================
    applytransform_gm = Node(ants.ApplyTransforms(input_image_type = 3,
                                               interpolation = 'NearestNeighbor',
                                               invert_transform_flags=[False, False]),
                          name='applytransform_gm')
    applytransform_gm.inputs.reference_image=template
    applytransform_gm.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    applytransform_d = Node(ants.ApplyTransforms(input_image_type = 3,
                                               interpolation = 'BSpline',
                                               invert_transform_flags=[False, False]),
                          name='applytransform_d')
    applytransform_d.inputs.reference_image=template
    applytransform_d.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    applytransform_db = Node(ants.ApplyTransforms(input_image_type = 3,
                                               interpolation = 'BSpline',
                                               invert_transform_flags=[False, False]),
                          name='applytransform_db')
    applytransform_db.inputs.reference_image=template
    applytransform_db.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    applytransform_dbn = Node(ants.ApplyTransforms(input_image_type = 3,
                                               interpolation = 'BSpline',
                                               invert_transform_flags=[False, False]),
                          name='applytransform_dbn')
    applytransform_dbn.inputs.reference_image=template
    applytransform_dbn.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    # NODE 5. tune down image to float
    # ================================
    changedt_gm = Node(fsl.ChangeDataType(output_datatype='short',
                                           out_file       ='gm_ribbon2mni.nii.gz'),
                                           name='changedt_gm')
    changedt_gm.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    changedt_d = Node(fsl.ChangeDataType(output_datatype='float',
                                           out_file       ='rest_denoised2mni.nii.gz'),
                                           name='changedt_d')
    changedt_d.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    changedt_db = Node(fsl.ChangeDataType(output_datatype='float',
                                           out_file       ='rest_denoised_bandpassed2mni.nii.gz'),
                                           name='changedt_db')
    changedt_db.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    changedt_dbn = Node(fsl.ChangeDataType(output_datatype='float',
                                           out_file       ='rest_denoised_bandpassed_normed2mni.nii.gz'),
                                           name='changedt_dbn')
    changedt_dbn.plugin_args={'submit_specs': 'request_memory = 20000'}
    
    # NODE 6. sink
    # ============
    sink = Node(nio.DataSink(parameterization=True, base_directory=out_dir),name='sink')
    
    mni.connect([ (scan_infosource, selectfiles, [('scan_id','scan_id')]),
                  (selectfiles, translist,           [('affine', 'in2'),('warp', 'in1')]),
                  (selectfiles, applytransform_d,      [('rest_d', 'input_image')]),
                  (translist, applytransform_d,        [('out', 'transforms')]),
                  (applytransform_d, changedt_d,         [('output_image', 'in_file')]),
                  (changedt_d, sink,                   [('out_file', 'preprocessed.func.pb05_mni.@restd_mni')]),
                  (selectfiles, applytransform_db,      [('rest_db', 'input_image')]),
                  (translist, applytransform_db,        [('out', 'transforms')]),
                  (applytransform_db, changedt_db,         [('output_image', 'in_file')]),
                  (changedt_db, sink,                   [('out_file', 'preprocessed.func.pb05_mni.@restdb_mni')]),
                  (selectfiles, applytransform_dbn,      [('rest_dbn', 'input_image')]),
                  (translist, applytransform_dbn,        [('out', 'transforms')]),
                  (applytransform_dbn, changedt_dbn,         [('output_image', 'in_file')]),
                  (changedt_dbn, sink,                   [('out_file', 'preprocessed.func.pb05_mni.@restdbn_mni')]),
                  (selectfiles, applytransform_gm,      [('gm', 'input_image')]),
                  (translist, applytransform_gm,        [('out', 'transforms')]),
                  (applytransform_gm, changedt_gm,         [('output_image', 'in_file')]),
                  (changedt_gm, sink,                   [('out_file', 'preprocessed.func.pb05_mni.@gm_ribbon_mni')]),
                ])
    
    mni.write_graph(dotfilename='mni.dot', graph2use='flat', format='pdf', simple_form=False)
    mni.run()
    #mni.run(plugin='MultiProc', plugin_args={'n_procs' : 4})
