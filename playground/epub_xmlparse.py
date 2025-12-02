import xml.etree.ElementTree as ET
from zipfile import ZipFile

file_name = "EPUBS/1984 (George Orwell) (Z-Library).epub"


with ZipFile(file_name, 'r') as epub_file:
    # open the epub file and find container.xml
    with epub_file.open('META-INF/container.xml') as container_xml:
        # read the contents of container.xml
        # print(container_xml.read().decode('utf-8'))
        xml_string = container_xml.read().decode('utf-8')

        # parse the xml string
        root = ET.fromstring(xml_string)

        # find content.opf file
        rootfile = root.find('.//{*}rootfile')
        print(rootfile.get('full-path'))

        ## Find the tags I need
        # print("Root tag:", root.tag)
        # print("Root attributes:", root.attrib)
        #
        # for child in root:
        #     print("Child tags:", child.tag)