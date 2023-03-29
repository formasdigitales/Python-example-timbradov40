# Python Ejemplo de Timbrado CFDI 4.0

<br/>
## Requerimientos
	* [Python versión 3.7+](https://www.python.org/downloads/)

	* Librerías
	   * [pem](https://pypi.org/project/pem/)
	    	> ``` pip install pem ```

		* [Zeep: Python SOAP Client](https://docs.python-zeep.org/en/master/)
			> ``` pip install zeep ```

		* [Cryptography](https://cryptography.io/en/latest/)
			> ``` pip install cryptography ```

		* [pyOpenssl](https://pypi.org/project/pyOpenSSL/)
			> ``` pip install pyOpenSSL ```

		* [pycryptodome](https://pypi.org/project/pycryptodome/)
			> ``` pip install pycryptodome```
<br/>

La clase **Timbradov40** contiene todos los métodos para poder procesar el xml deseado a timbrar.

<br/>

## Métodos de la clase Timbradov40

## def procesaxml(self,path_xml):
Método principal para poder realizar el timbrado del xml, contiene la llamadas a los demas métodos **cargaCertificados** el cual nos ayudara a procesar el 
archivo pem que contiene el certificado, **generaSello** nos permitirá crear el sello o la firma del xml una vez creada la cadena original, 
por último se hace el llamado al método **timbrar** para mandar a timbrar el xml al webservice de formas digitales.

```Python

	def procesaxml(self,path_xml):
		data = ET.parse(path_xml)
		comprobante = data.getroot()
		fechacurrent = datetime.today().strftime('%Y-%m-%dT%H:%M:%S') #se obtiene la fecha actual del sistema con el formato solicitado por el SAT
		comprobante.set("Fecha",fechacurrent) #se le asigna la fecha al xml
		self.comprobante = comprobante 
		self.cargaCertificados(self.certificado)#Se llama al metodo cargaCertificados
		self.generaSello()#Una vez que ya esten los datos Certificado,NoCertificado en el xml y generada la cadena original se llama al metodo generaSello
		self.timbrar(self.usuario,self.password)#Se llama al metodo timbrar

```

## def cargaCertificados(self,path_cer):
Contiene la llamada al método **get_num_certificado** el cual nos regresá el número del certificado una vez asignado el número de certificado y el certificado al xml se llama al método **generaCadenaOriginal**.

```Python

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

```	

## def generaCadenaOriginal(self,comprobante):
Permite crear la cadena original del xml una vez que ya tenga la información completa.

```Python

	def generaCadenaOriginal(self,comprobante):
		xslt = ET.parse(self.path_xslt)#Se parsea el contenido del xslt
		transform = ET.XSLT(xslt)
		cadena_original = transform(comprobante)#se crea la cadena orignal
		self.cadenaoriginal = str(cadena_original).replace("\n","")#se eliminan los saltos de linea y se guarda en memoria

```

## def generaSello(self):
Permite generar el sello despues de haber realizado la cadena original, se carga la llave privada en formato pem una vez obtenido el sello se le asigna al 
xml.

```Python

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

```

## def timbrar(self,usuario,password):
Una vez sellado el xml se hace el llamado al método **timbrar** en donde se hace el cliente del WSDL de formas digitales, se crea el objeto accesos y se manda a nuestro servicio para procesarlo, si no hay ningún problema regresara el xml timbrado se guardara en un documento y se mostrará en consola, en caso de que exista algún error se muestra en pantalla y se guardara en documento.

```Python

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

```

## def guardaXML(self,path,xml):
Permite guardar el xml timbrado o el error en caso de existir.
```Python

	def guardaXML(self,path,xml):
		file = codecs.open(path,'w','UTF-8')
		file.write(xml)
		file.close()

```
