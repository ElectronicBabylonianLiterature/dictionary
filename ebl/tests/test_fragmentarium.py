# pylint: disable=W0621
import datetime
from freezegun import freeze_time
import pydash
import pytest


COLLECTION = 'fragments'


@pytest.fixture
def another_fragment(fragment):
    return pydash.defaults({
        '_id': '2',
        'accession': 'accession-no-match',
        'cdliNumber': 'cdli-no-match'
    }, fragment)


def test_create(database, fragmentarium, fragment):
    fragment_id = fragmentarium.create(fragment)

    assert database[COLLECTION].find_one({'_id': fragment_id}) == fragment


def test_find(database, fragmentarium, fragment):
    database[COLLECTION].insert_one(fragment)

    assert fragmentarium.find(fragment['_id']) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(KeyError):
        fragmentarium.find('unknown id')


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragmentarium, fragment, user_profile):
    fragmentarium.create(fragment)
    updates = {
        'transliteration': 'the transliteration',
        'notes': fragment['notes']
    }

    fragmentarium.update_transliteration(
        fragment['_id'],
        updates,
        user_profile
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': updates['transliteration'],
            'notes': fragment['notes'],
            'record': [{
                'user': user_profile['https://ebabylon.org/eblName'],
                'type': 'Transliteration',
                'date': datetime.datetime.utcnow().isoformat()
            }]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(fragmentarium, fragment, user_profile):
    fragmentarium.create(pydash.defaults({
        'transliteration': 'old transliteration'
    }, fragment))
    updates = {
        'transliteration':  'the updated transliteration',
        'notes': 'updated notes'
    }

    fragmentarium.update_transliteration(
        fragment['_id'],
        updates,
        user_profile
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': updates['transliteration'],
            'notes': updates['notes'],
            'record': [{
                'user': user_profile['https://ebabylon.org/eblName'],
                'type': 'Revision',
                'date': datetime.datetime.utcnow().isoformat()
            }]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


def test_update_notes(fragmentarium, fragment, user_profile):
    fragmentarium.create(fragment)
    updates = {
        'transliteration': fragment['transliteration'],
        'notes': 'new nites'
    }

    fragmentarium.update_transliteration(
        fragment['_id'],
        updates,
        user_profile
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': fragment['transliteration'],
            'notes': updates['notes'],
            'record': []
        },
        fragment
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(database,
                   fragmentarium,
                   fragment,
                   user_profile,
                   make_changelog_entry):
    fragment_id = fragmentarium.create(fragment)
    updates = {
        'transliteration':  'the updated transliteration',
        'notes': 'updated notes'
    }

    fragmentarium.update_transliteration(
        fragment_id,
        updates,
        user_profile
    )

    expected_changelog = make_changelog_entry(
        COLLECTION,
        fragment_id,
        pydash.pick(fragment, 'transliteration', 'notes'),
        updates
    )
    assert database['changelog'].find_one(
        {'resource_id': fragment_id},
        {'_id': 0}
    ) == expected_changelog


def test_update_update_transliteration_not_found(fragmentarium, user_profile):
    # pylint: disable=C0103
    with pytest.raises(KeyError):
        fragmentarium.update_transliteration(
            'unknown.number',
            'transliteration',
            user_profile
        )


def test_statistics(database, fragmentarium, fragment):
    database[COLLECTION].insert_many([
        pydash.defaults({'_id': '1', 'transliteration': '''1. first line
$ingore

'''}, fragment),
        pydash.defaults({'_id': '2', 'transliteration': '''@ignore
1'. second line
2'. third line
@ignore
1#. fourth line'''}, fragment),
        pydash.defaults({'_id': '3', 'transliteration': ''}, fragment),
    ])

    assert fragmentarium.statistics() == {
        'transliteratedFragments': 2,
        'lines': 4
    }


def test_statistics_no_fragments(fragmentarium):
    assert fragmentarium.statistics() == {
        'transliteratedFragments': 0,
        'lines': 0
    }


def test_search_finds_by_id(database,
                            fragmentarium,
                            fragment,
                            another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragmentarium.search(fragment['_id']) == [fragment]


def test_search_finds_by_accession(database,
                                   fragmentarium,
                                   fragment,
                                   another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragmentarium.search(fragment['accession']) == [fragment]


def test_search_finds_by_cdli(database,
                              fragmentarium,
                              fragment,
                              another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragmentarium.search(fragment['cdliNumber']) == [fragment]


def test_search_not_found(fragmentarium):
    assert fragmentarium.search('K.1') == []


def test_search_signs(database,
                      fragmentarium,
                      transliterated_fragment,
                      another_fragment):
    database[COLLECTION].insert_many([
        transliterated_fragment,
        another_fragment
    ])

    assert fragmentarium.search_signs([
        ['DIŠ', 'UD']
    ]) == [transliterated_fragment]
    assert fragmentarium.search_signs([['KU']]) == [transliterated_fragment]
    assert fragmentarium.search_signs([['UD']]) == [transliterated_fragment]
    assert fragmentarium.search_signs([
        ['GI₆', 'DIŠ'],
        ['U', 'BA', 'MA']
    ]) == [transliterated_fragment]
    assert fragmentarium.search_signs([['IGI', 'UD']]) == []
