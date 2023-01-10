import os
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse, HttpResponse, JsonResponse
from pdf2image import convert_from_path
from pyzbar import pyzbar
from PIL import Image
from pyzbar import pyzbar
import cv2
import jwt
import re

inputFilePath = "input\\temp.pdf"
imageFolderPath = "pdf2image"
popplerBinFolderPath = "poppler-0.68.0\\bin"

def deleteAllTempFiles():
    if(os.path.exists(inputFilePath)):
        os.remove(inputFilePath)
    for f in os.listdir(imageFolderPath):
        os.remove(os.path.join(imageFolderPath, f))
def processQRData(qrdata):
    qrdata['data'] = qrdata['data'].replace("\"", "")
    strdata = qrdata.get('data')
    strdata = strdata.replace('{','')
    strdata = strdata.replace('}','')
    listData = strdata.split(',')
    processedData = {}
    for l in listData:
        pair = l.split(':')
        if(pair[0]=='IrnDt'):
            processedData[pair[0]] = pair[1] + ':' + pair[2] + ':' +pair[3]
        else:
            processedData[pair[0]] = pair[1]
    qrdata['data'] = processedData
    return qrdata

def extractInvQrData(n):
    try:
        jsonArray = {}
        jsonArray["status"]='1'
        for i in range(n):
            # read images using opencv
            img = cv2.imread(imageFolderPath + '//page' + str(i) + '.jpg')
            try:
                barcodes = pyzbar.decode(img)
                
            except:
                return {'status':'0','message':'no qrcode found'}
            bdata = barcodes[0].data.decode()
            qrdata = jwt.decode(bdata, options={"verify_signature": False})
            jsonArray['page'+str(i+1)] = processQRData(qrdata)
        return jsonArray
    except:
        return {'status':'0','error_message':'file format didn\'t match with standerd e-invoice format'}


# convert string to list - ewaybillqrcode data
def convert_to_List(string):
    li = list(string.split(" "))
    if(re.search("^[a-zA-Z]", li[1]) != None):
        for k in range(2,len(li)-1):
            li[1]= li[1]+ ' '+ li[k]
        while(len(li)!=3):
            li.pop(2)
    else:
        li[1] = li[1] + ' ' + li[2] + li[3]
        li[4] = li[4] + ' ' + li[5] + li[6]
        li.pop(2)
        li.pop(2)
        li.pop(3)
        li.pop(3)
    return li

# extract field and row values for ewaybill qrcode data
def fields_And_Values_Qrcodedata(Qrcode_data):
    header = ['EwbNo', 'EwbDt', 'Gen Dt', 'EwbValidTill', 'Gen By']
    # list of regular exp. to remove
    Reglist = ['EwbNo :-','EWB No.:', 'EwbDt : -','Gen. Dt.:', 'EwbValidTill :-', 'Gen By:-','Gen. By:']
    i = 1
    try:
        jsonarray = {}
        jsonarray["status"]='1'
        for d in Qrcode_data:
            for rg in Reglist:
                d = d.replace(rg, ' ')
            res = " ".join(d.split())
            res_list = convert_to_List(res)
            if(len(res_list)==3):
                res_list.insert(1,' ')
                res_list.insert(3,' ')
            else:
                res_list.insert(2,' ')
            row = dict(zip(header, res_list))
            jsonarray['page'+str(i)] = row
            i += 1
        return jsonarray
    except:
        return {'status':'0','error_message':'file format didn\'t match with standerd Eway Bill format'}

def extractEwayBillQrData(n):
    qrCodeData = []
    for i in range(n):
        # read images using opencv
        img = cv2.imread(imageFolderPath + '//page'+ str(i) + '.jpg')
        try:
            barcodes = pyzbar.decode(img)
            bdata = barcodes[0].data.decode()
        except:
            return {'status':'0','error_message':'file format didn\'t match with standerd Eway Bill format'}
        qrCodeData.append(bdata)
    return qrCodeData

# converting pdf to image
def convert_pdf_to_image(inputFilePath):
    images = convert_from_path(inputFilePath, poppler_path=popplerBinFolderPath)
    for i in range(len(images)):
        # Save pages as images
        images[i].save(imageFolderPath + '//page' + str(i) + '.jpg', 'JPEG')
    return len(images)

   
@csrf_exempt
def InvPdf(request):
    if(request.method=='POST'):
        try:
            file = request.FILES["file"]
            
            #Veryfying the extension
            ext = os.path.splitext(file.name)[1] 

            # If extension is other than PDF report error
            if (ext.lower() != ".pdf" and ext.lower() != ".jpg"):
                return JsonResponse({'status':'0','error_message':'Unsupported file extension.'})
        except:
            return JsonResponse({'status':'0','error_message':'file not found'})
 
        if(ext.lower() == ".pdf"):
            with open(inputFilePath, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            n = convert_pdf_to_image(inputFilePath)
            qrCodeData = extractInvQrData(n)
            deleteAllTempFiles()
            return JsonResponse(qrCodeData)

        elif(ext.lower() == ".jpg"):
            with open(imageFolderPath + '//page0.jpg', 'wb') as f:
                    for chunk in file.chunks():
                         f.write(chunk)
            qrCodeData = extractInvQrData(1)
            deleteAllTempFiles()
            return JsonResponse(qrCodeData)
    
@csrf_exempt
def EwayBillPdf(request):
    if(request.method=='POST'):
        try:
            file = request.FILES["file"]
            
            #Veryfying the extension
            ext = os.path.splitext(file.name)[1] 

            # If extension is other than PDF report error
            if (ext.lower() != ".pdf" and ext.lower() != ".jpg"):
                return JsonResponse({'status':'0','error_message':'Unsupported file extension.'})


        except:
            return JsonResponse({'status':'0','error_message':'file not found'})

        if(ext.lower() == ".pdf"):
                with open(inputFilePath, 'wb') as f:
                    for chunk in file.chunks():
                         f.write(chunk)

                n = convert_pdf_to_image(inputFilePath)
                qrCodeData = extractEwayBillQrData(n)
                # extract fields and values from qrcodedata
                jsonData = fields_And_Values_Qrcodedata(qrCodeData)
                deleteAllTempFiles()
                return JsonResponse(jsonData)
            
        elif(ext.lower() == ".jpg"):
                with open(imageFolderPath + '//page0.jpg', 'wb') as f:
                    for chunk in file.chunks():
                         f.write(chunk)
                qrCodeData = extractEwayBillQrData(1)
                # extract fields and values from qrcodedata
                jsonData = fields_And_Values_Qrcodedata(qrCodeData)
                deleteAllTempFiles()
                return JsonResponse(jsonData)


    
