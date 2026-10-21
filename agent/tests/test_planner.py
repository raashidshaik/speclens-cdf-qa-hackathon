from planner import extract, plan

def test_requirement_text_is_preserved():
    r = extract('## Transfers\n- Reject zero amounts.\n## Out of scope\n- Real payments.')
    assert len(r)==1 and r[0]['text']=='Reject zero amounts.'

def test_semantic_routing_uses_content_not_position():
    r = plan('## Contract\n- Profile displays a masked email.\n- Transfer source and destination amount.\n- Log out and protect dashboard access.')
    assert [v['capability'] for v in r] == ['profile','transfer','session']

def test_unknown_words_do_not_create_false_confidence():
    assert plan('## Contract\n- Xylophone zebra.')[0]['similarity']==0
