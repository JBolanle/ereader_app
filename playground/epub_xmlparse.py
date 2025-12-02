import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from zipfile import ZipFile

file_name = "EPUBS/1984 (George Orwell) (Z-Library).epub"

NAMESPACES = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
}

with ZipFile(file_name, 'r') as epub_file:
    ## open the epub file and read contents
    opf_content = epub_file.read('content.opf').decode('utf-8')
    root = ET.fromstring(opf_content)

    ## find metadata elements and print
    def find_metadata(root: Element, field_name: str, namespaces: dict[str, str]) -> str | None:
        """Try to find a metadata field in both DC namespaces."""
        elem = root.find(f'.//dcterms:{field_name}', namespaces)
        if elem is None:
            elem = root.find(f'.//dc:{field_name}', namespaces)
        return elem.text if elem is not None else None

    title = find_metadata(root, 'title', NAMESPACES)
    author = find_metadata(root, 'creator', NAMESPACES)
    language = find_metadata(root, 'language', NAMESPACES)

    print(title)
    print(author)
    print(language)

    # # find title and print
    # title_elem = root.find('.//dc:title', NAMESPACES)
    # if title_elem is not None:
    #     print(f'Title: {title_elem.text}')
    # else:
    #     print('No title or not found in dc')
    #
    # # find author and print
    # author_elem = root.find('.//dc:creator', NAMESPACES)
    # if author_elem is not None:
    #     print(f'Author: {author_elem.text}')
    # else:
    #     print('No author or not found in dc')

    # # open the epub file and find container.xml
    # with epub_file.open('META-INF/container.xml') as container_xml:
    #     ## read the contents of container.xml
    #     # print(container_xml.read().decode('utf-8'))
    #     xml_string = container_xml.read().decode('utf-8')
    #
    #     ## parse the xml string
    #     root = ET.fromstring(xml_string)
    #
    #     ## find content.opf file
    #     rootfile = root.find('.//{*}rootfile')
    #     print(rootfile.get('full-path'))
    #
    #     ## Find the tags I need
    #     # print("Root tag:", root.tag)
    #     # print("Root attributes:", root.attrib)
    #     #
    #     # for child in root:
    #     #     print("Child tags:", child.tag)

