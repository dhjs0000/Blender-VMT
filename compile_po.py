try:
    import polib
except ImportError:
    import pip
    pip.main(['install', 'polib'])
    import polib

def compile_po_to_mo(po_file, mo_file):
    po = polib.pofile(po_file)
    po.save_as_mofile(mo_file)

compile_po_to_mo('lang/zh_CN/LC_MESSAGES/messages.po', 'lang/zh_CN/LC_MESSAGES/messages.mo')
compile_po_to_mo('lang/en_US/LC_MESSAGES/messages.po', 'lang/en_US/LC_MESSAGES/messages.mo')