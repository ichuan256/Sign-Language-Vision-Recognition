"""Train float students on immutable source-held-out teacher data; human accuracy remains separate."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import statistics
import sys
import time
os.environ.setdefault('TF_USE_LEGACY_KERAS','1')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS','4')
os.environ.setdefault('TF_NUM_INTEROP_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
from project.scripts.keypoints.build_hand_student import build
from vision.keypoints.student_data import load_dataset,augment,coordinate_metrics,digest,training_partitions


def evaluate(predictions,targets,masks,records):
    report={}
    for origin,key in [('teacher','teacher_agreement'),('human','human_accuracy')]:
        indices=[i for i,r in enumerate(records) if r['pose_source']==origin]
        report[key]=coordinate_metrics(predictions[indices],targets[indices],masks[indices]) if indices else None
        report[origin+'_fingertip_metrics']=coordinate_metrics(predictions[indices],targets[indices],masks[indices],point_indices=(4,8,12,16,20)) if indices else None
    by_group={}
    for group in sorted({r['split_group'] for r in records}):
        ix=[i for i,r in enumerate(records) if r['split_group']==group]
        by_group[group]=coordinate_metrics(predictions[ix],targets[ix],masks[ix])
    report['per_source_group_supervision_agreement']=by_group
    report['macro_source_group_NME']=statistics.mean(v['mean_normalized_error'] for v in by_group.values() if v) if any(by_group.values()) else None
    fast=[i for i,r in enumerate(records) if r['pose_source']=='human' and r.get('scenario')=='fast_motion']
    report['human_fast_motion_accuracy']=coordinate_metrics(predictions[fast],targets[fast],masks[fast]) if fast else None
    report['human_test_unique_frames']=len({(r['source_sha256'],r['source_frame']) for r in records if r['pose_source']=='human'})
    return report


def predict(model,images,batch):
    return np.concatenate([model(images[i:i+batch],training=False).numpy() for i in range(0,len(images),batch)])


def main():
    import tensorflow as tf
    import tf_keras as keras
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--reviews',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--sizes',type=int,nargs='+',default=[96,128])
    p.add_argument('--epochs',type=int,default=15);p.add_argument('--batch-size',type=int,default=16)
    p.add_argument('--patience',type=int,default=12);p.add_argument('--bn-momentum',type=float,default=.9)
    p.add_argument('--seed',type=int,default=20261026)
    p.add_argument('--disable-presence',action='store_true',help='Coordinate pilot only; keep presence loss off despite a tiny negative seed')
    p.add_argument('--mask-outside-source',action='store_true',help='Mask teacher points projecting outside the original source image; retain manual labels')
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp training output required')
    if a.epochs<1 or a.batch_size<1 or a.patience<1 or not 0<a.bn_momentum<1 or any(s not in (96,128) for s in a.sizes):raise ValueError('Invalid training config')
    images,y,m,records,data_report=load_dataset(a.data,a.reviews,mask_outside_source=a.mask_outside_source)
    partition=training_partitions(y,m,records,a.disable_presence)
    train=partition['train'];validation=partition['coordinates']['validation'];test=partition['coordinates']['test']
    if min(len(train),len(validation),len(test))<5:raise ValueError('Need at least five labelled ROIs in every source split')
    presence_enabled=partition['presence_enabled'];handedness_enabled=partition['handedness_enabled'];active=partition['active_masks']
    spec_path=ROOT/'project/algo/keypoints/hand_student_v1.json';spec=json.loads(spec_path.read_text())
    mean_shape=np.divide((y[train,:63]*m[train,:63]).sum(0),m[train,:63].sum(0),out=np.zeros(63,np.float32),where=m[train,:63].sum(0)>0)
    out.mkdir(parents=True);runs=[]
    for size in a.sizes:
        keras.backend.clear_session();keras.utils.set_random_seed(a.seed);rng=np.random.default_rng(a.seed)
        model=build(spec,size);head=model.get_layer('coordinate_presence_handedness_head')
        for layer in model.layers:
            if isinstance(layer,keras.layers.BatchNormalization):layer.momentum=a.bn_momentum
        kernel,bias=head.get_weights();kernel=rng.normal(0,.001,kernel.shape).astype(np.float32);bias[:63]=mean_shape
        head.set_weights([kernel,bias]);optimizer=keras.optimizers.Adam(learning_rate=1e-3,clipnorm=1.)
        @tf.function
        def train_step(x,t,mask):
            with tf.GradientTape() as tape:
                prediction=model(x,training=True)
                delta=tf.abs(prediction[:,:63]-t[:,:63]);huber=tf.where(delta<.03,.5*delta*delta,.03*(delta-.015))
                weights=mask[:,:63]*tf.constant([1.,1.,.1]*21)[None,:]
                loss=tf.reduce_sum(huber*weights)/(.03*tf.maximum(1.,tf.reduce_sum(weights)))
                for column,factor in [(63,.05),(64,.005)]:
                    ce=tf.nn.sigmoid_cross_entropy_with_logits(labels=t[:,column],logits=prediction[:,column])
                    loss+=factor*tf.reduce_sum(ce*mask[:,column])/tf.maximum(1.,tf.reduce_sum(mask[:,column]))
            gradients=tape.gradient(loss,model.trainable_variables)
            optimizer.apply_gradients(zip(gradients,model.trainable_variables));return loss
        def prepared(indices,jitter):
            result=[augment(images[i],y[i],active[i],size,np.random.default_rng(a.seed+int(i)) if jitter else None) for i in indices]
            return tuple(np.stack([r[j] for r in result]) for j in range(3))
        vx,vy,vm=prepared(validation,True)
        vr=[records[i] for i in validation];history=[];best=float('inf');best_weights=None;best_epoch=0;start=time.perf_counter()
        for epoch in range(a.epochs):
            order=rng.permutation(train);losses=[]
            for offset in range(0,len(order),a.batch_size):
                batch=[augment(images[i],y[i],active[i],size,rng) for i in order[offset:offset+a.batch_size]]
                bx,by,bm=[np.stack([r[j] for r in batch]) for j in range(3)]
                losses.append(float(train_step(bx,by,bm)))
            val=evaluate(predict(model,vx,a.batch_size),vy,vm,vr);score=val['macro_source_group_NME']
            if score is None or not np.isfinite(score):raise RuntimeError('Validation non-finite')
            history.append(dict(epoch=epoch+1,loss=float(np.mean(losses)),validation_jitter_macro_source_NME=score))
            print('STUDENT',size,'EPOCH',epoch+1,'loss',round(history[-1]['loss'],6),'VAL_NME',round(score,5),flush=True)
            if score<best:best=score;best_weights=model.get_weights();best_epoch=epoch+1
            elif epoch+1-best_epoch>=a.patience:break
        model.set_weights(best_weights);path=out/f'hand_student_{size}_FLOAT_PILOT.keras';model.save(path)
        evaluations={}
        for split,indices in [('validation',validation),('test',test)]:
            rr=[records[i] for i in indices];evaluations[split]={}
            for jitter,name in [(False,'canonical_ROI'),(True,'fixed_jitter_ROI')]:
                xx,tt,mm=prepared(indices,jitter);prediction=predict(model,xx,a.batch_size)
                evaluations[split][name]=evaluate(prediction,tt,mm,rr)
                baseline=np.zeros_like(prediction);baseline[:,:63]=mean_shape
                evaluations[split][name]['train_mean_shape_baseline']=evaluate(baseline,tt,mm,rr)
        test_human=evaluations['test']['canonical_ROI']['human_accuracy']
        run=dict(input_size=size,epochs=len(history),best_epoch=best_epoch,elapsed_s=time.perf_counter()-start,
            history=history,evaluation=evaluations,model_sha256=digest(path),model_file=path.name,
            trained=True,quantized=False,HLS_validated=False,board_deployed=False,
            human_accuracy_gate_passed=False,
            promotion_blockers=['Independent human test set and reviewed negative coverage have not been accepted',
                'No QAT, integer/HLS parity, detector or board latency validation'])
        # Human numbers, if present, are reported without automatic promotion from a tiny pilot.
        run['human_test_metrics_present']=test_human is not None;runs.append(run)
    report=dict(status='float_pseudo_label_pilot_trained_not_deployable',runs=runs,seed=a.seed,
        BN_momentum=a.bn_momentum,patience=a.patience,epochs_requested=a.epochs,
        dataset_sha256=digest(a.data/'dataset.json'),records_sha256=data_report['records_sha256'],
        review_sha256=digest(a.reviews) if a.reviews else None,student_spec_sha256=digest(spec_path),
        trained_ROIs=len(train),validation_ROIs=len(validation),test_ROIs=len(test),
        selected_record_counts=dict(Counter(r['split'] for r in records)),
        reviewed_negative_train_ROIs=partition['negative_train_used'],reviewed_negative_train_ROIs_available=partition['negative_train_available'],
        presence_loss_disabled_explicitly=a.disable_presence,presence_loss_enabled=presence_enabled,
        source_exterior_masking_enabled=a.mask_outside_source,
        source_exterior_points_masked=sum(r.get('source_exterior_points_masked',0) for r in records),
        handedness_loss_enabled=handedness_enabled,
        limitations=['Source-video group holdout; performer IDs remain unknown',
            'Pseudo-label agreement is not manually annotated landmark accuracy',
            'Presence head loss is disabled until human-reviewed negative training examples exist',
            'Fixed-jitter holdout is an augmentation diagnostic, not additional independent samples',
            'Best epoch selected only on validation; test evaluated once after training'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('TRAINING_COMPLETE',out,flush=True)


if __name__=='__main__':main()
