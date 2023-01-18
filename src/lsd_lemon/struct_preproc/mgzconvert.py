from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import os


'''
Workflow to extract relevant output from freesurfer directory
'''

def create_mgzconvert_pipeline(name='mgzconvert'):
    
    # workflow
    mgzconvert = Workflow(name='mgzconvert')

    #inputnode 
    inputnode=Node(util.IdentityInterface(fields=['fs_subjects_dir',
                                                  'fs_subject_id',
                                                  ]),
                   name='inputnode')
    
    #outputnode
    outputnode=Node(util.IdentityInterface(fields=['anat_head',
                                                   'anat_brain',
                                                   'func_mask',
                                                   'wmseg',
                                                   'wmedge',
                                                   'gmseg']),
                    name='outputnode')
    

    # import files from freesurfer
    fs_import = Node(interface=nio.FreeSurferSource(),
                     name = 'fs_import')
    
    
    # convert Freesurfer T1 file to nifti
    head_convert=Node(fs.MRIConvert(out_type='niigz',
                                     out_file='T1.nii.gz'),
                       name='head_convert')
    
    
    # convert Freesurfer brain.finalsurf file to nifti
    # grab finalsurf file
    def grab_brain(fs_subjects_dir, fs_subject_id):
        import os
        brainfile = os.path.join(fs_subjects_dir, fs_subject_id, 
                                 'mri', 'brain.finalsurfs.mgz')
        return os.path.abspath(brainfile)
    
    brain_grab=Node(util.Function(input_names=['fs_subjects_dir', 
                                               'fs_subject_id'],
                                  output_names=['brain_file'],
                                  function=grab_brain),
                    name='brain_grab')
    
    brain_convert=Node(fs.MRIConvert(out_type='niigz',
                                     out_file='T1_brain.nii.gz'),
                       name='brain_convert')

   # create brainmask from aparc+aseg with single dilation for functional data
   # DIFFERENT APPROACHES TO MASK THE FUNCTIONAL AND STRUCTURAL DATA 
   # ARE USED FOR HISTORIC REASONS
    def get_aparc_aseg(files):
        for name in files:
            if 'aparc+aseg' in name:
                return name

    funcmask = Node(fs.Binarize(min=0.5,
                                 dilate=1,
                                 out_type='nii.gz'),
                   name='funcmask')


    # fill holes in mask, smooth, rebinarize
    fillholes = Node(fsl.maths.MathsCommand(args='-fillh -s 3 -thr 0.1 -bin',
                                            out_file='func_mask.nii.gz'),
                     name='fillholes')


    # cortical and cerebellar white matter volumes to construct wm edge
    # [lh cerebral wm, lh cerebellar wm, rh cerebral wm, rh cerebellar wm, brain stem]
    wmseg = Node(fs.Binarize(out_type='nii.gz',
                             match = [2, 7, 41, 46, 16],
                             binary_file='T1_brain_wmseg.nii.gz'), 
                name='wmseg')

    # GM ribbon 
    # Modification by JGC on Oct 2021
    # To get the numbers needed in this mask, I needed to do the following:
    # 1) Convert the Freesurfer outputs of one subject to AFNI format using
    #    @SUMA_Make_Spec_FS -sid sub-010091 -NIFTI -fspath /data/SFIMJGC_Introspec/prcs_data_nipype/Freesurfer/sub-010091
    # 2) Select the numbers that cover GM regions looking at the following file:
    # /data/SFIMJGC_Introspec/prcs_data_nipype/Freesurfer/sub-010091/./SUMA/fs_table.niml.lt
    # If additional structures are needed. This would be the place to start.
    # =======================================================================
    gmseg = Node(fs.Binarize(out_type='nii.gz',
                             match=[10,11,12,13,17,18,19,20,49,50,51,52,53,54,55,56,96,97,136,137,218,1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020,1021,1022,1023,1024,1025,1026,1027,1028,1029,1030,1031,1032,1033,1034,1035,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030,2031,2032,2033,2034,2035,1100,1101,1102,1103,1104,1200,1201,1202,1205,1206,1207,1210,1211,1212,1105,1106,1107,1108,1109,1110,1111,1112,1113,1114,1115,1116,1117,1118,1119,1120,1121,1122,1123,1124,1125,1126,1127,1128,1129,1130,1131,1132,1133,1134,1135,1136,1137,1138,1139,1140,1141,1142,1143,1144,1145,1146,1147,1148,1149,1150,1151,1152,1153,1154,1155,1156,1157,1158,1159,1160,1161,1162,1163,1164,1165,1166,1167,1168,1169,1170,1171,1172,1173,1174,1175,1176,1177,1178,1179,1180,1181,2100,2101,2102,2103,2104,2105,2106,2107,2108,2109,2110,2111,2112,2113,2114,2115,2116,2117,2118,2119,2120,2121,2122,2123,2124,2125,2126,2127,2128,2129,2130,2131,2132,2133,2134,2135,2136,2137,2138,2139,2140,2141,2142,2143,2144,2145,2146,2147,2148,2149,2150,2151,2152,2153,2154,2155,2156,2157,2158,2159,2160,2161,2162,2163,2164,2165,2166,2167,2168,2169,2170,2171,2172,2173,2174,2175,2176,2177,2178,2179,2180,2181,2200,2201,2202,2205,2206,2207,2210,2211,2212,9000,9001,9002,9003,9004,9005,9006,9500,9501,9502,9503,9504,9505,9506,11100,11101,11102,11103,11104,11105,11106,11107,11108,11109,11110,11111,11112,11113,11114,11115,11116,11117,11118,11119,11120,11121,11122,11123,11124,11125,11126,11127,11128,11129,11130,11131,11132,11133,11134,11135,11136,11137,11138,11139,11140,11141,11142,11143,11144,11145,11146,11147,11148,11149,11150,11151,11152,11153,11154,11155,11156,11157,11158,11159,11160,11161,11162,11163,11164,11165,11166,11167,11168,11169,11170,11171,11172,11173,11174,11175,12100,12101,12102,12103,12104,12105,12106,12107,12108,12109,12110,12111,12112,12113,12114,12115,12116,12117,12118,12119,12120,12121,12122,12123,12124,12125,12126,12127,12128,12129,12130,12131,12132,12133,12134,12135,12136,12137,12138,12139,12140,12141,12142,12143,12144,12145,12146,12147,12148,12149,12150,12151,12152,12153,12154,12155,12156,12157,12158,12159,12160,12161,12162,12163,12164,12165,12166,12167,12168,12169,12170,12171,12172,12173,12174,12175],
                             binary_file='gm.nii.gz'),name='gmseg')
 
    # make edge from wmseg  to visualize coregistration quality
    edge = Node(fsl.ApplyMask(args='-edge -bin',
                              out_file='T1_brain_wmedge.nii.gz'),
                name='edge')

    # connections
    mgzconvert.connect([(inputnode, fs_import, [('fs_subjects_dir','subjects_dir'),
                                                ('fs_subject_id', 'subject_id')]),
                        (fs_import, head_convert, [('T1', 'in_file')]),
                        (inputnode, brain_grab, [('fs_subjects_dir', 'fs_subjects_dir'),
                                                 ('fs_subject_id', 'fs_subject_id')]),
                        (brain_grab, brain_convert, [('brain_file', 'in_file')]),
                        (fs_import, wmseg, [(('aparc_aseg', get_aparc_aseg), 'in_file')]),
                        (fs_import, gmseg, [(('aparc_aseg', get_aparc_aseg), 'in_file')]),
                        (fs_import, funcmask, [(('aparc_aseg', get_aparc_aseg), 'in_file')]),
                        (funcmask, fillholes, [('binary_file', 'in_file')]),
                        (wmseg, edge, [('binary_file', 'in_file'),
                                       ('binary_file', 'mask_file')]),
                        (head_convert, outputnode, [('out_file', 'anat_head')]),
                        (fillholes, outputnode, [('out_file', 'func_mask')]),
                        (brain_convert, outputnode, [('out_file', 'anat_brain')]),
                        (wmseg, outputnode, [('binary_file', 'wmseg')]),
                        (gmseg, outputnode, [('binary_file', 'gmseg')]),
                        (edge, outputnode, [('out_file', 'wmedge')]),
                        ])
                                         
    return mgzconvert
