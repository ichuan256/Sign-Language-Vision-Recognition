"""Exact content binds paths; declared absence is different from integrity success."""
import pytest
from project.scripts.check_layout import verify_protected,sha256
from vision.scripts.dataset.reconcile_media_paths import reconcile,restored_original,restored_bindings


def test_reconcile_keeps_missing_and_does_not_guess_identical_copies():
    expected=[dict(path='old',sha256='a'),dict(path='missing',sha256='b'),dict(path='ambiguous',sha256='c')]
    actual={p:dict(sha256=h,bytes=1) for p,h in [('renamed','a'),('c1','c'),('c2','c'),('missing','wrong')]}
    rows,extras=reconcile(expected,actual)
    assert [(r['path'],r['availability']) for r in rows]==[('renamed','present'),('missing','missing'),('ambiguous','ambiguous')]
    assert {r['path'] for r in extras}=={'c1','c2','missing'}


def test_exact_expected_original_path_disambiguates_duplicate_content():
    actual={p:dict(sha256='original') for p in ('a','b')}
    row=dict(old_expected_path='b',old_expected_sha256='original')
    assert restored_original(row,actual,{'original'})=='b'
    assert restored_original(dict(row,old_expected_path='gone'),actual,{'original'}) is None
    assert restored_original(row,actual,{'different_audit'}) is None


def test_restoration_lineage_survives_reconciling_from_current_pending_table():
    row=dict(status='original_audit_SHA_restored_not_in_approved_subset',path='current_original',
        previous_path='old_variant_path',prior_pending_sha256='variant',sha256='original',old_expected_sha256='original')
    assert restored_bindings([row])=={('variant','old_variant_path'):'current_original'}
    with pytest.raises(ValueError,match='lineage'):restored_bindings([dict(row,sha256='wrong')])


def inventory(tmp_path):
    path=tmp_path/'vision/video/present.mp4';path.parent.mkdir(parents=True);path.write_bytes(b'unchanged')
    rows=[dict(path='vision/video/present.mp4',sha256=sha256(path),bytes=9,availability='present'),
        dict(path='vision/video/absent.mp4',sha256='0'*64,bytes=5,availability='missing')]
    return dict(declared_missing=1),rows,path


def test_only_explicit_available_mode_allows_declared_absences(tmp_path):
    info,rows,_=inventory(tmp_path)
    with pytest.raises(ValueError,match='Archive incomplete'):verify_protected(tmp_path,info,rows)
    present,missing=verify_protected(tmp_path,info,rows,available_only=True)
    assert len(present)==len(missing)==1


@pytest.mark.parametrize('problem',['changed','lost','extra','reappeared'])
def test_available_mode_still_rejects_unrecorded_changes(tmp_path,problem):
    info,rows,path=inventory(tmp_path)
    if problem=='changed':path.write_bytes(b'corrupted')
    elif problem=='lost':path.unlink()
    elif problem=='extra':(path.parent/'extra.mp4').write_bytes(b'new')
    else:(path.parent/'absent.mp4').write_bytes(b'restored')
    with pytest.raises(ValueError):verify_protected(tmp_path,info,rows,available_only=True)
