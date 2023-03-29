
import os
import pem
import base64
import zeep
import codecs
from lxml import etree as ET
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from OpenSSL import crypto
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
class timbradov40:
	
	#CARGA DEL XLST PARA GENERACION DE LA CADENA ORIGINAL V 4.0
	path_xslt = "resources/cadenaoriginal_4_0.xslt"
	# WSDL PRUEBAS 	 (FORMAS DIGITALES)
	wsdl_url = "http://dev33.facturacfdi.mx/WSTimbradoCFDIService?wsdl" 

	#Se inicializan las variables con los datos que se le envian al crear un objeto de la clase timbradov40
	def __init__(self,xml,certificado,llave_privada,usuario,password,Debug=None):
		self.certificado=certificado
		self.xml=xml
		self.llave_privada=llave_privada
		self.usuario = usuario
		self.password = password
		if Debug is not None:
			self.DEBUG = Debug
	#Metodo principal que va a procesar el xml enviado
	def procesaxml(self,path_xml):
		data = ET.parse(path_xml)
		comprobante = data.getroot()
		fechacurrent = datetime.today().strftime('%Y-%m-%dT%H:%M:%S') #se obtiene la fecha actual del sistema con el formato solicitado por el SAT
		comprobante.set("Fecha",fechacurrent) #se le asigna la fecha al xml
		self.comprobante = comprobante 
		self.cargaCertificados(self.certificado)#Se llama al metodo cargaCertificados
		self.generaSello()#Una vez que ya esten los datos Certificado,NoCertificado en el xml y generada la cadena original se llama al metodo generaSello
		self.timbrar(self.usuario,self.password)#Se llama al metodo timbrar

	def cargaCertificados(self,path_cer):
		with open(path_cer,'rb') as f:
			certfile = f.read()
		
		cert = x509.load_pem_x509_certificate(certfile)	#Se crea un objeto certificado de la clase X509
		no_certificado = self.get_num_certificado(hex(cert.serial_number)) #se realiza el llamado al metodo para obtener el numero del certificado y asignarlo al xml
		comprobante = self.comprobante
		comprobante.set("NoCertificado",no_certificado)
		certificado = certfile.decode('utf-8').replace('-----BEGIN CERTIFICATE-----','').replace('-----END CERTIFICATE-----','').replace('\n','')
		comprobante.set("Certificado",certificado)#Se le asigna el certificado al xml
		self.generaCadenaOriginal(comprobante)#Se llama al metodo generaCadenaOriginal
	
	def get_num_certificado(self,serial_hex):
		no_certificado = ""
		serial_str = str(serial_hex)
		if(len(serial_str) % 2) == 1 :
			serial_str = '' + serial_str

		serial_len = len(serial_str) // 2
		for index in range(serial_len):
			start_index = (index * 2)
			end_index = start_index + 2
			aux = serial_str[start_index:end_index]

			if 'x' != aux[1]:
				no_certificado = no_certificado + aux[1]
		return no_certificado

	def generaCadenaOriginal(self,comprobante):
		xslt = ET.parse(self.path_xslt)#Se parsea el contenido del xslt
		transform = ET.XSLT(xslt)
		cadena_original = transform(comprobante)#se crea la cadena orignal
		self.cadenaoriginal = str(cadena_original).replace("\n","")#se eliminan los satos de linea y se guarda en memoria

	def generaSello(self):
		privateKey = False
		with open(self.llave_privada,'r')as myfile_key:
			privateKey = RSA.import_key(myfile_key.read())#Se leen los datos del archivo enviado que lleva la llave privada y se crea un objeto RSA

		digest2 = SHA256.new()
		digest2.update(self.cadenaoriginal.encode('UTF-8'))
		signer = PKCS1_v1_5.new(privateKey)
		sig = signer.sign(digest2)#Se genera el sello en base64
		sello = base64.b64encode(sig).decode('UTF-8')#Se decodifica de base64 a String para asignarla al xml
		self.comprobante.set("Sello",sello)

	def timbrar(self,usuario,password):
		cliente_formas = zeep.Client(wsdl = self.wsdl_url)#Se crea un cliente soap del WSDL de formas digitales
		try:
			#Timbra cfdi
			accesos_type = cliente_formas.get_type("ns1:accesos")
			accesos_formas = accesos_type(usuario=usuario,password=password)#se crea el objeto de accesos

			cfdi_timbrado = cliente_formas.service.TimbrarCFDI(accesos = accesos_formas,comprobante=ET.tostring(self.comprobante).decode('UTF-8'))#Se le envian los parametros solicitados los cuales son accesos y comprobante o xml en una cadena

			if cfdi_timbrado['error'] == None: #Si no ocurrio ningún error al momento de timbrar el xml generará un xml timbrado y se plasmará en la consola
				xmlTimbrado = cfdi_timbrado['xmlTimbrado']
				print(xmlTimbrado)
				filename = "xmltimbrado.xml"
			else:#En caso contrario se genera un xml con el error e igual se mostrara en la consola
				xmlTimbrado = cfdi_timbrado['codigoError'] + ' - ' + cfdi_timbrado['error']
				print(xmlTimbrado)
				filename = "xml_error.xml"
			path = os.path.dirname(os.path.abspath(__file__)) + '/resources/'+filename
			self.guardaXML(path,xmlTimbrado)

		except Exception as exception:
			print("Message %s" % exception)

	def guardaXML(self,path,xml):
		file = codecs.open(path,'w','UTF-8')
		file.write(xml)
		file.close()

path = os.path.dirname(os.path.abspath(__file__)) + '/resources/'
#CARGA XML DE PRUEBAS
path_xml=path + "cfdi_v40_generico.xml"

#CARGA CERTIFICADO DE PRUEBAS
path_cer= "resources/EKU9003173C9_certificado.pem"

#CARGA LLAVE PRIVADA DE PRUEBAS
path_key=path + "EKU9003173C9_llavePrivada.pem"

#usuario y contraseña de pruebas de nuestro servicio de timbrado
usuario='pruebasWS'
password='pruebasWS'

timbradoP = timbradov40(path_xml,path_cer,path_key,usuario,password)
timbradoP.procesaxml(path_xml)