import datetime
import json
from freezegun import freeze_time
from ebl.fragmentarium.fragment import Fragment
from ebl.fragmentarium.fragment import Record
from ebl.fragmentarium.fragment import Folios
from ebl.fragmentarium.transliterations import Transliteration


def test_to_dict(fragment):
    new_fragment = Fragment(fragment.to_dict())

    assert new_fragment.to_dict() == fragment.to_dict()


def test_to_dict_for(fragment, user):
    assert fragment.to_dict_for(user) == {
        **fragment.to_dict(),
        'folios': fragment.folios.filter(user).entries
    }


def test_equality(fragment, transliterated_fragment):
    new_fragment = Fragment(fragment.to_dict())

    assert new_fragment == fragment
    assert new_fragment != transliterated_fragment


def test_hash(fragment):
    assert hash(fragment) == hash(json.dumps(fragment.to_dict()))


def test_accession(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.accession == data['accession']


def test_cdli_number(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.cdli_number == data['cdliNumber']


def test_transliteration(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.transliteration ==\
        Transliteration(data['transliteration'], data['notes'])


def test_record(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.record == Record(data['record'])


def test_folios(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.folios == Folios(data['folios'])


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragment, user):
    transliteration = Transliteration('x x', fragment.transliteration.notes)

    updated_fragment = fragment.update_transliteration(
        transliteration,
        user
    )
    expected_fragment = Fragment({
        **fragment.to_dict(),
        'transliteration': transliteration.atf,
        'record': [{
            'user': user.ebl_name,
            'type': 'Transliteration',
            'date': datetime.datetime.utcnow().isoformat()
        }]
    })

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(transliterated_fragment, user):
    transliteration =\
        Transliteration('1. x x\n2. x', 'updated notes', signs='X X\nX')
    updated_fragment = transliterated_fragment.update_transliteration(
        transliteration,
        user
    )

    expected_fragment = Fragment({
        **transliterated_fragment.to_dict(),
        'transliteration': transliteration.atf,
        'notes': transliteration.notes,
        'signs': transliteration.signs,
        'record': [
            *transliterated_fragment.to_dict()['record'],
            {
                'user': user.ebl_name,
                'type': 'Revision',
                'date': datetime.datetime.utcnow().isoformat()
            }
        ]
    })

    assert updated_fragment == expected_fragment


def test_update_notes(fragment, user):
    transliteration =\
        Transliteration(fragment.transliteration.atf, 'new notes')

    updated_fragment = fragment.update_transliteration(
        transliteration,
        user
    )

    expected_fragment = Fragment({
        **fragment.to_dict(),
        'notes': transliteration.notes
    })

    assert updated_fragment == expected_fragment


def test_add_matching_lines(transliterated_fragment):
    with_matching_lines =\
        transliterated_fragment.add_matching_lines([['7\'. šu/gid']])

    assert with_matching_lines.to_dict() == {
        **transliterated_fragment.to_dict(),
        'matching_lines': [['7\'. šu/gid']]
    }


def test_filter_folios(user):
    wgl_folio = {
        'name': 'WGL',
        'number': '1'
    }
    folios = Folios([
        wgl_folio,
        {
            'name': 'XXX',
            'number': '1'
        },
    ])
    expected = Folios([
        wgl_folio
    ])

    assert folios.filter(user) == expected
