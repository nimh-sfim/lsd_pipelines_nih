from nipype.pipeline.engine import Workflow, Node 
import nipype.interfaces.utility as util
from nipype.interfaces.mipav.developer import JistIntensityMp2rageMasking, MedicAlgorithmSPECTRE2010

'''
Workflow to remove noisy background from MP2RAGE images 
AND SKULLSTRIP unsing cbstools
==============================
adapt import in run_structural.py to "structural_cbstools" to use this.

'''


def create_mp2rage_pipeline(name='mp2rage'):
    
    # workflow
    mp2rage = Workflow('mp2rage')
    
    # inputnode 
    inputnode=Node(util.IdentityInterface(fields=['inv2',
                                                  'uni',
                                                  't1map']),
               name='inputnode')
    
    # outputnode                                     
    outputnode=Node(util.IdentityInterface(fields=['uni_masked',
                                                   'background_mask',
                                                   'uni_stripped',
                                                   #'skullstrip_mask',
                                                   #'uni_reoriented'
                                                   ]),
                name='outputnode')

    # JAVIER: remove background noise
    background = Node(JistIntensityMp2rageMasking(outMasked=True,
                                            outMasked2=True,
                                            outSignal2=True,
                                            inSkip='true',
                                            inMasking='binary',
                                            inBackground='exponential', innoniterative='false'),
                                            name='background')
    # ORIGINAL: remove background noise
    #background = Node(JistIntensityMp2rageMasking(outMasked=True,
    #                                        outMasked2=True,
    #                                        outSignal2=True), 
    #                  name='background')
    # end of ORIGINAL
    
    # skullstrip
    strip = Node(MedicAlgorithmSPECTRE2010(outStripped=True,
                                           outMask=True,
                                           outOriginal=True,
                                           inOutput='true',inOutput2='true', inOutput3='true',inOutput4='true',inOutput5="Trilinear",
                                           inFind='true',
                                           inMMC=4, inMMC2=2,
                                           inImage='T1_MPRAGE',
                                           inRun='true',
                                           inInitial=5, inInitial2=0.35,
                                           inResample='false',
                                           inMinimum=0.1,
                                           inInhomogeneity='false',
                                           inSmoothing=0.02,
                                           inBackground=0.001,
                                           inSkip='false',inSubsample='true',inUse='true', inMultithreading='false',
                                           inNumber=2, inNumber2=3,inMultiple=10,inFine=6, inCoarse=15, inMaximum=30, inMinimum2=-30, inApply='All',
                                           inDegrees='Affine - 12', inCost='Correlation ratio', inRegistration="Trilinear"),
                 name='strip')
    
    # connections
    mp2rage.connect([(inputnode, background, [('inv2', 'inSecond'),
                                              ('t1map', 'inQuantitative'),
                                              ('uni', 'inT1weighted')]),
                     (background, strip, [('outMasked2','inInput')]),
                     (background, outputnode, [('outMasked2','uni_masked'),
                                               ('outSignal2','background_mask')]),
                    (strip, outputnode, [('outStripped','uni_stripped'),
                                         #('outMask', 'skullstrip_mask'),
                                         #('outOriginal','uni_reoriented')
                                         ])
                     ])
    
    
    return mp2rage
