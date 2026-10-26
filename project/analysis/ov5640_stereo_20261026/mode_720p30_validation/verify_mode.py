from pathlib import Path
import copy, importlib.util, json, re
r=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('camera_generator',r/'project/scripts/ov5640/generate_startup_table.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
c=g.make_contract();report=g.audit(c)
assert c['mode']['width']==1280 and c['mode']['height']==720
assert c['table_count']==308 and c['mode']['fps_target']==30
assert report['pclk_hz_candidate']==84000000 and report['pclk_spec_margin_hz']==12000000
known=json.loads((g.ANALYSIS/'known_config_contract.json').read_text(encoding='utf-8'))
text=(r/'project/fpga/rtl/ov5640_stereo/ov5640_known_config_table.v').read_text(encoding='utf-8')
actual=re.findall(r"reg_addr=16'h([0-9a-f]+); reg_value=8'h([0-9a-f]+)",text)
assert dict(actual)=={x['address']:x['value'] for x in known['items']}
assert len(actual)==27
checks=['final mode/clock arithmetic','27-item known table equals independent contract']
for kind in ['PLL revert','output dimension','binning disabled','metadata clock','early stream','chip ID write']:
    bad=copy.deepcopy(c)
    if kind=='PLL revert':
        for x in bad['items']:
            if x['address']=='3035':x['value']='10'
    elif kind=='output dimension':
        for x in bad['items']:
            if x['address']=='3808':x['value']='07'
    elif kind=='binning disabled':
        for x in bad['items']:
            if x['address']=='3820':x['value']='00';x['mask']='01'
    elif kind=='metadata clock':bad['mode']['pclk_hz_candidate']=168000000
    else:bad['items'].append(dict(address='3008' if kind=='early stream' else '300a',value='02',mask='ff'))
    try:g.audit(bad)
    except ValueError:checks.append('reject '+kind)
    else:raise AssertionError('Audit accepted '+kind)
report['negative_and_consistency_checks']=checks
Path(__file__).with_name('contract_verification.json').write_text(json.dumps(report,indent=2)+chr(10),encoding='utf-8')
print(json.dumps(report,indent=2))
