from ebl.fragment.folios import Folios, Folio


def test_filter_folios(user):
    wgl_folio = Folio('WGL', '1')
    folios = Folios((
        wgl_folio,
        Folio('XXX', '1')
    ))
    expected = Folios((
        wgl_folio,
    ))

    assert folios.filter(user) == expected
