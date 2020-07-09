import pytest  # pyre-ignore
from mockito import verify  # pyre-ignore

from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory, \
    ReferenceFactory, BibliographyEntryFactory
from ebl.tests.factories.fragment import FragmentFactory


COLLECTION = "bibliography"


def test_search_container_short_collection_number(bibliography, bibliography_repository,
                                                  when):
    bibliography_entry = BibliographyEntryFactory.build()
    container_title = bibliography_entry["container-title-short"]
    collection_number = bibliography_entry["collection-number"]
    query = f"{container_title} {collection_number}"
    (
        when(bibliography_repository).query_by_author_year_and_title(
            container_title,
            int(collection_number),
            None)
        .thenReturn([])
    )
    (
        when(bibliography_repository).query_by_container_title_and_collection_number(
            container_title,
            collection_number)
        .thenReturn([bibliography_entry])
    )
    assert [bibliography_entry] == bibliography.search(query)


def test_search_author_title_year(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    author = bibliography_entry["author"][0]["family"]
    year = bibliography_entry["issued"]["date-parts"][0][0]
    title = bibliography_entry["title"]
    query = f"{author} {year} {title}"
    (
        when(bibliography_repository).query_by_author_year_and_title(
            author,
            year,
            title)
        .thenReturn([bibliography_entry])
    )
    (
        verify(bibliography_repository, 0).
        query_by_container_title_and_collection_number(
            author,
            str(year))

    )
    assert [bibliography_entry] == bibliography.search(query)


def test_find(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenReturn(bibliography_entry)
    )
    assert bibliography.find(bibliography_entry["id"]) == bibliography_entry


def test_inject_document_in_references(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    fragment_1 = FragmentInfo.of(FragmentFactory.build(
        number='K.1',
        references=(ReferenceFactory.build(id='RN.0'),))
    )
    fragment_2 = FragmentInfo.of(FragmentFactory.build(
        number='K.2',
        references=(ReferenceFactory.build(id='RN.1'), ReferenceFactory.build(id='RN.2')))
    )
    fragment_expected_1 = fragment_1.set_references([
        fragment_1.references[0].set_document(bibliography_entry)
    ])
    fragment_expected_2 = fragment_2.set_references([
        fragment_2.references[0].set_document(bibliography_entry),
        fragment_2.references[1].set_document(bibliography_entry),
    ])

    (
        when(bibliography_repository)
        .query_by_id("RN.0")
        .thenReturn(bibliography_entry)
    )
    (
        when(bibliography_repository)
        .query_by_id("RN.1")
        .thenReturn(bibliography_entry)
    )
    (
        when(bibliography_repository)
        .query_by_id("RN.2")
        .thenReturn(bibliography_entry)
    )

    assert bibliography.inject_document_in_references([fragment_1, fragment_2]) == [
        fragment_expected_1, fragment_expected_2
    ]


def test_create(bibliography, bibliography_repository, user, changelog, when,
                mongo_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            {"_id": bibliography_entry["id"]},
            mongo_entry(),
        ).thenReturn()
    )
    (
        when(bibliography_repository)
        .create(bibliography_entry)
        .thenReturn()
    )

    bibliography.create(bibliography_entry, user)


def test_create_duplicate(bibliography, user, when, changelog,bibliography_repository,
                          mongo_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            {"_id": bibliography_entry["id"]},
            mongo_entry(),
        ).thenReturn()
    )
    (
        when(bibliography_repository)
        .create(bibliography_entry)
        .thenRaise(DuplicateError)
    )
    with pytest.raises(DuplicateError):
        bibliography.create(bibliography_entry, user)


def test_entry_not_found(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.find(bibliography_entry["id"])


def test_update(bibliography, bibliography_repository,
                user, when, changelog, mongo_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenReturn(bibliography_entry)
    )
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            mongo_entry(),
            mongo_entry(),
        ).thenReturn()
    )
    (
        when(bibliography_repository)
        .update(bibliography_entry)
        .thenReturn()
    )
    bibliography.update(bibliography_entry, user)


def test_update_not_found(bibliography_repository, bibliography, user, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.update(bibliography_entry, user)


def test_validate_references(bibliography_repository, bibliography, user, changelog,
                             when):
    reference = ReferenceWithDocumentFactory.build()

    (
        when(bibliography)
        .find(reference.id)
        .thenReturn(reference)
    )
    bibliography.validate_references([reference])


def test_validate_references_invalid(bibliography_repository, bibliography,
                                     user, changelog, when):
    valid_reference = ReferenceWithDocumentFactory.build()
    first_invalid = ReferenceWithDocumentFactory.build()
    second_invalid = ReferenceWithDocumentFactory.build()
    bibliography.create(valid_reference.document, user)
    (
        when(bibliography)
        .find(valid_reference.id)
        .thenReturn(valid_reference)
    )
    (
        when(bibliography)
        .find(first_invalid.id)
        .thenRaise(NotFoundError)
    )
    (
        when(bibliography)
        .find(second_invalid.id)
        .thenRaise(NotFoundError)
    )

    expected_error = (
        "Unknown bibliography entries: "
        f"{first_invalid.id}"
        ", "
        f"{second_invalid.id}"
        "."
    )

    with pytest.raises(DataError, match=expected_error):
        bibliography.validate_references(
            [first_invalid, valid_reference, second_invalid]
        )
