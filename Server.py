import socketserver
import datetime
import numpy as np
import cv2
from tensorflow.python.keras.models import load_model, model_from_json
from tensorflow.python.keras.preprocessing import image

class classification():
    
    def __init__(self):
        #self.net = load_model("OrchidClassification.h5", compile = False) #compile=false確實可以加快一點速度，大概縮短三秒
        json_file = open("OrchidClassificationJson.json", "r") #可以縮短大概四秒
        loaded_model_json = json_file.read()
        json_file.close()
        self.net = model_from_json(loaded_model_json)
        self.net.load_weights("OrchidClassificationWeights.h5")
        print("model loaded!!")
        self.cls_list = ['1095', '1785', '1793', '2267', '2389', '2439', '2447', '2464', '2473', '906'] 

    def classifier(self, img):
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis = 0)
        pred = self.net.predict(x)[0]
        top_inds = pred.argsort()[::-1][:10]
        counter = 0
        for i in top_inds:
            counter = counter + 1
            #print('{:.3f}  {}'.format(pred[i], self.cls_list[i]))
            if counter == 1:
                choice = i
                break
        flowerName = self.cls_list[choice]
        confidence = '{:.3f}'.format(pred[choice])
        return flowerName, confidence



class MyTCPHandler(socketserver.BaseRequestHandler):
    
    
    def handle(self):
        print("RECIEVING....")
        imageData = []
        try:
            while True:
                data=self.request.recv(1024) #拿到客戶端發送的數據
                if data[-3:] == b'EOD':
                    data = data[:-1]
                    data = data[:-1]
                    data = data[:-1]
                    imageData.extend(data)
                    break
                else:
                    imageData.extend(data)
            
            recvImage = np.asarray(bytearray(imageData), dtype="uint8")
            recvImage = cv2.imdecode(recvImage, cv2.IMREAD_COLOR)
            #cv2.namedWindow("Image")
            #cv2.imshow("Image", recvImage)
            #cv2.waitKey(5000)
            #cv2.destroyAllWindows()
            recvImage = recvImage[...,::-1].astype(np.float32)
            print("接收完成")
            print("Classifying...")
            global c
            c = classification()
            flowerName, confidence = c.classifier(recvImage) #這句有問題- 已解決(return太複雜)
            print(flowerName, confidence)
            print("Finished classifying!")
            
            print("Sending Message!!")
            self.request.sendall((flowerName + '\0').encode("utf-8")) #這兩句有問題, 在這邊crash掉 - 已解決(要進行編碼，且在後面加上'\0'方便切割字串)
            self.request.send(confidence.encode("utf-8"))
            print("Message sent!!")
            
            
            
            
        except Exception:
            print(self.client_address,"DISCONNECT")
        finally:
            self.request.close()    #異常之後關閉連接
 
    #before handle,建立連接：
    def setup(self):
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(now_time)
        print("CONNECTION ESTABLISHED：",self.client_address)
 
    # finish run after handle
    def finish(self):
        print("CONNECTION RELEASED")




if __name__=="__main__":
    HOST,PORT = "",2998
    server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()   #一直運行
 
