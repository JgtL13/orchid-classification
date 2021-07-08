package com.example.orchidclassification;

import androidx.appcompat.app.AppCompatActivity;

import android.Manifest;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.view.animation.Animation;
import android.view.animation.AnimationUtils;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.Socket;
import java.util.ArrayList;

public class MainActivity extends AppCompatActivity {

    //private static int SPLASH_SCREEN =5000;

    private ImageView imageView;
    private Bitmap selectedImage;
    private TextView textView;
    private Button button;
    private String species;
    private String probability;
    ProgressDialog progressDialog;

    private  Button BtnMove;
    private void moveToFlowerInformation(){
        Intent intent = new Intent(MainActivity.this, FlowerInformations.class);
        startActivity(intent);
    }
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        BtnMove = findViewById(R.id.FList);
        BtnMove.setOnClickListener(new View.OnClickListener() {
                                       @Override
                                       public void onClick(View v) {
                                           moveToFlowerInformation();
                                       }
                                   });

        button = findViewById(R.id.button);
        imageView = findViewById(R.id.imageView);
        textView = findViewById(R.id.textView);
        textView.setText("");
        //FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                selectImage(MainActivity.this);
            }
        });
        if (Build.VERSION.SDK_INT >= 23){
            int REQUEST_CODE_CONTACT = 101;
            String[] permissions = {Manifest.permission.READ_EXTERNAL_STORAGE};
            for (String str : permissions) {
                if (this.checkSelfPermission(str) != PackageManager.PERMISSION_GRANTED) {
                    this.requestPermissions(permissions, REQUEST_CODE_CONTACT);
                }
            }
        }
    }

    private void selectImage(Context context) {
        final CharSequence[] options = {"拍攝照片", "從相簿選擇", "取消"};
        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle("選擇照片");
        builder.setItems(options, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int item) {
                if(options[item].equals("拍攝照片")) {
                    Intent takePicture = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                    startActivityForResult(takePicture, 0);
                } else if(options[item].equals("從相簿選擇")) {
                    Intent pickPhoto = new Intent(Intent.ACTION_PICK, android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
                    startActivityForResult(pickPhoto, 1);
                } else if(options[item].equals("取消")) {
                    dialog.dismiss();
                }
            }
        });
        builder.show();
    }

    //send image function
    public void sendImgMsg(DataOutputStream out, Bitmap image) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        image.compress(Bitmap.CompressFormat.JPEG, 100, baos);
        byte[] byteArray = baos.toByteArray();
        out.write(byteArray);
        out.flush();

    }

    // send text function
    public void sendTextMsg(DataOutputStream out, String msg) throws IOException {
        byte[] bytes = msg.getBytes();
        out.write(bytes);
    }

    public void updateTextView(String species, String probability) {
        float f1 = Float.parseFloat(probability);
        float percentage = f1 * 100;
        //final String confidence = Float.toString("%.3f", percentage);
        final String confidence = String.format("%.1f", percentage);
        if(percentage >= 80) {
            textView.setText("\n此品種為目前資料庫中登錄的品種之一\n"
                            + "品種代碼: " + species + "\n\n"
                            + "參考機率值: " + confidence + "%\n");
        }
        else {
            textView.setText("\n此品種為目前資料庫中尚未登錄的品種\n"
                            + "與之最接近之品種代碼: " + species + "\n\n"
                            + "參考機率值: " + confidence + "%\n");
        }


    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {

        if(resultCode != RESULT_CANCELED) {

            switch (requestCode) {
                case 0:
                    if (resultCode == RESULT_OK && data != null) {
                        selectedImage = (Bitmap) data.getExtras().get("data");
                        imageView.setImageBitmap(selectedImage);
                    }

                    break;
                case 1:
                    if (resultCode == RESULT_OK && data != null) {
                        Uri selectedImageUri = data.getData();
                        String[] filePathColumn = {MediaStore.Images.Media.DATA};
                        if (selectedImageUri != null) {
                            Cursor cursor = getContentResolver().query(selectedImageUri,
                                    filePathColumn, null, null, null);
                            if (cursor != null) {
                                cursor.moveToFirst();

                                int columnIndex = cursor.getColumnIndex(filePathColumn[0]);
                                String picturePath = cursor.getString(columnIndex);
                                imageView.setImageBitmap(BitmapFactory.decodeFile(picturePath));

                                selectedImage = BitmapFactory.decodeFile(picturePath); //convert to bitmap

                                cursor.close();
                            }
                        }

                    }
                    break;
            }

            selectedImage = Bitmap.createScaledBitmap(selectedImage, 224, 224, false);
            progressDialog = ProgressDialog.show(MainActivity.this, "品種辨識中", "請稍候片刻", true);

            //establish connection and send picture to server
            new Thread() {
                Socket socket;
                String host = "120.113.173.82";
                int port = 2998;

                public void run() {
                    try {
                        //建立連接
                        socket = new Socket(host, port);
                        DataOutputStream out = new DataOutputStream(socket.getOutputStream());
                        BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                        sendImgMsg(out, selectedImage);
                        sendTextMsg(out, "EOD");

                        String inLine = in.readLine();
                        String[] all = inLine.split("\0");
                        species = all[0];
                        probability = all[1];

                        System.out.println("Species: " + species);
                        System.out.println("Probability: " + probability);

                        //float f1 = Float.parseFloat(probability);
                        //float percentage = f1 * 100;
                        //final String confidence = Float.toString(percentage);
                        //System.out.println("Confidence: " + confidence);

                        Handler refresh = new Handler(Looper.getMainLooper());
                        refresh.post(new Runnable() {
                            public void run() {
                                //updateTextView(species, confidence);
                                updateTextView(species, probability);
                                progressDialog.dismiss();
                            }
                        });
                        out.close();
                        in.close();
                        socket.close();

                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
            }.start();
        }
    }
}
