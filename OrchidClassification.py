from tensorflow.keras import backend as K
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Flatten, Dense, Dropout
#from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications import ResNet50V2
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

# 資料路徑
DATASET_PATH = 'C:/ResNet2020'

# 影像大小
IMAGE_SIZE = (224, 224)

# 影像類別數
NUM_CLASSES = 10

# 若 GPU 記憶體不足，可調降 batch size 或凍結更多層網路
BATCH_SIZE = 40

# 凍結網路層數
FREEZE_LAYERS = 2

# Epoch 數
NUM_EPOCHS = 40

# 模型輸出儲存的檔案
WEIGHTS_FINAL = 'OrchidClassificationModel.h5'

# 透過 data augmentation 產生訓練與驗證用的影像資料
train_datagen = ImageDataGenerator(rotation_range = 40,         #照片隨機旋轉-40度~40度
                                   width_shift_range = 0.2,     #水平移動寬度的0.2倍
                                   height_shift_range = 0.2,    #垂直移動高度的0.2倍
                                   shear_range = 0.2,           #每個點的x軸或y軸固定不變，
                                                               #另一個軸就按照比例偏移
                                   zoom_range = 0.2,            #在長或寬進行縮放
                                   horizontal_flip = True,      #水平翻轉
                                   vertical_flip = False,        #垂直翻轉
                                   fill_mode = 'constant',      #填充模式，有空白的地方就用顏色填滿
                                   cval = 100) 
#train_datagen = ImageDataGenerator()
train_batches = train_datagen.flow_from_directory(DATASET_PATH + '/trainResize',
                                                  target_size = IMAGE_SIZE,
                                                  interpolation = 'bicubic',
                                                  class_mode = 'categorical',
                                                  shuffle = True,
                                                  batch_size = BATCH_SIZE)

valid_datagen = ImageDataGenerator()
valid_batches = valid_datagen.flow_from_directory(DATASET_PATH + '/validResize',
                                                  target_size = IMAGE_SIZE,
                                                  interpolation = 'bicubic',
                                                  class_mode = 'categorical',
                                                  shuffle = False,
                                                  batch_size = BATCH_SIZE)
test_datagen = ImageDataGenerator()
test_batches = test_datagen.flow_from_directory(DATASET_PATH + '/testResize',
                                                target_size = IMAGE_SIZE,
                                                interpolation = 'bicubic',
                                                class_mode = 'categorical',
                                                shuffle = False,
                                                batch_size = BATCH_SIZE)

# 輸出各類別的索引值
for cls, idx in train_batches.class_indices.items():
    print('Class #{} = {}'.format(idx + 1, cls))

# 以訓練好的 ResNet50 為基礎來建立模型，
# 捨棄 ResNet50 頂層的 fully connected layers
net = ResNet50V2(include_top = False, weights = 'imagenet', input_tensor = None,
               input_shape = (IMAGE_SIZE[0], IMAGE_SIZE[1], 3))
x = net.output
x = Flatten()(x)

# 增加 DropOut layer
x = Dropout(0.5)(x)

# 增加 Dense layer，以 softmax 產生個類別的機率值
output_layer = Dense(NUM_CLASSES, activation='sigmoid', name='sigmoid')(x) #try sigmoid, softmax 總何必等於100%

# 設定凍結與要進行訓練的網路層
net_final = Model(inputs = net.input, outputs = output_layer)
for layer in net_final.layers[:FREEZE_LAYERS]:
    layer.trainable = False
for layer in net_final.layers[FREEZE_LAYERS:]:
    layer.trainable = True

# 使用 Adam optimizer，以較低的 learning rate 進行 fine-tuning
#net_final.compile(optimizer = Adam(lr=1e-5),
#                 loss = 'categorical_crossentropy', metrics=['accuracy'])
net_final.compile(optimizer = Adam(lr=0.00001),
                 loss = 'categorical_crossentropy', metrics=['accuracy'])
# 輸出整個網路結構
#print(net_final.summary())

# 訓練模型
history = net_final.fit(train_batches,
                        steps_per_epoch = train_batches.samples // BATCH_SIZE,
                        validation_data = valid_batches,
                        validation_steps = valid_batches.samples // BATCH_SIZE,
                        epochs = NUM_EPOCHS,
                        )


# 儲存訓練好的模型
net_final.save(WEIGHTS_FINAL)

# 載入訓練好的模型
net = load_model(WEIGHTS_FINAL)

plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'valid'], loc='upper left')
plt.show()

# summarize history for loss 
plt.plot(history.history['loss']) 
plt.plot(history.history['val_loss']) 
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'valid'], loc='upper left') 
plt.show()

Y_pred = net.predict_generator(test_batches, test_batches.samples // BATCH_SIZE+1)
y_pred = np.argmax(Y_pred, axis=1)
print('Confusion Matrix')
print(confusion_matrix(test_batches.classes, y_pred))
print('Classification Report')
target_names = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
print(classification_report(test_batches.classes, y_pred, target_names=target_names))

predictions = net.predict(test_batches)
predictions = np.argmax(predictions,axis=1)
print(predictions)

score, acc = net.evaluate(test_batches)
print('Test loss:', score)
print('Test accuracy:', acc)