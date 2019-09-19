from ebl.sign_list.sign import Sign, SignListRecord, Value


def test_sign():
    name = 'KUR'
    lists = (SignListRecord('FOO', '123'),)
    values = (Value('kur', 8), Value('ruk'))
    sign = Sign(name,
                lists=lists,
                values=values)

    assert sign.name == name
    assert sign.lists == lists
    assert sign.values == values


def test_standardization_abz():
    name = 'ABZ'
    number = '123'
    sign = Sign('KUR', lists=(SignListRecord(name, number), ))
    assert sign.standardization == f'{name}{number}'


def test_standardization_multiple_abz():
    name = 'ABZ'
    number = '123'
    sign = Sign('KUR', lists=(SignListRecord(name, number),
                              SignListRecord(name, '999')))
    assert sign.standardization == f'{name}{number}'


def test_standardization_no_abz():
    sign = Sign('KUR')
    assert sign.standardization == sign.name