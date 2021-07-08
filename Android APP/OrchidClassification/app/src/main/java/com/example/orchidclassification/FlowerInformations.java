package com.example.orchidclassification;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class FlowerInformations extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_flower_informations);

        WebView webview = (WebView) findViewById(R.id.WebPage);
        webview.getSettings().setJavaScriptEnabled(true);
        //WebView.setWebViewClient(new WebViewClient()); //不調用系統瀏覽器
        webview.loadUrl("https://sites.google.com/view/ncyu-resnet-2020/lists");
    }
}
