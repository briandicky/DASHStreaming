package com.example.mosquito.dashplayer;


import android.media.MediaPlayer;
import android.net.Uri;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.MediaController;
import android.widget.VideoView;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;

public class MainActivity extends AppCompatActivity
{
    private VideoView vidView;
    private MediaController vidControl;
    private Button low, medium, high;
    private Uri vidUri;
    private String concatLow, concatMedium, concatHigh;
    private ArrayList<String> lowQueue = new ArrayList<String>();
    private ArrayList<String> mediumQueue = new ArrayList<String>();
    private ArrayList<String> highQueue = new ArrayList<String>();
    private ArrayList<String> current = new ArrayList<String>();
    private String vidAddress = "http://140.114.77.170:8000/";
    private int index;
    private boolean startflag = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        vidView = (VideoView) findViewById(R.id.myVideo);
        vidControl = new MediaController(this);
        vidControl.setAnchorView(vidView);
        vidView.setMediaController(vidControl);

        low = (Button) findViewById(R.id.lowQuality);
        medium = (Button) findViewById(R.id.mediumQuality);
        high = (Button) findViewById(R.id.highQuality);


        // Using thread to read url and parsing file content into arraylist
        Thread waitThread;
        waitThread = new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url_playlist = new URL(vidAddress + "playlist.m3u8");
                    try {
                        BufferedReader input = new BufferedReader(new InputStreamReader(url_playlist.openStream()));

                        String inputLine;
                        while ( (inputLine = input.readLine()) != null ) {
                            if (inputLine.contains("BANDWIDTH=1280000"))
                                concatLow = input.readLine();
                            if (inputLine.contains("BANDWIDTH=2560000"))
                                concatMedium = input.readLine();
                            if (inputLine.contains("BANDWIDTH=5120000"))
                                concatHigh = input.readLine();
                        }

                        input.close();
                    } catch (IOException e) {
                    }

                    URL url_low = new URL(vidAddress + concatLow);
                    try {
                        BufferedReader input = new BufferedReader(new InputStreamReader(url_low.openStream()));

                        String inputLine;
                        while ( (inputLine = input.readLine()) != null ) {
                            if (inputLine.contains("low"))
                                lowQueue.add(inputLine);
                        }

                        input.close();
                    } catch (IOException e) {
                    }

                    URL url_medium = new URL(vidAddress + concatMedium);
                    try {
                        BufferedReader input = new BufferedReader(new InputStreamReader(url_medium.openStream()));

                        String inputLine;
                        while ( (inputLine = input.readLine()) != null ) {
                            if (inputLine.contains("medium"))
                                mediumQueue.add(inputLine);
                        }

                        input.close();
                    } catch (IOException e) {
                    }

                    URL url_high = new URL(vidAddress + concatHigh);
                    try {
                        BufferedReader input = new BufferedReader(new InputStreamReader(url_high.openStream()));

                        String inputLine;
                        while ( (inputLine = input.readLine()) != null ) {
                            if (inputLine.contains("high"))
                                highQueue.add(inputLine);
                        }

                        input.close();
                    } catch (IOException e) {
                    }
                } catch (IOException e) {
                }
            }
        });waitThread.start();

        // Low button onclick listener
        low.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!startflag) {
                    index = 0;
                    startflag = true;

                    vidUri = Uri.parse(vidAddress + lowQueue.get(index));
                    vidView.setVideoURI(vidUri);
                    vidView.start();
                }

                current = lowQueue;
            }
        });

        // Medium button onclick listener
        medium.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!startflag) {
                    index = 0;
                    startflag = true;

                    vidUri = Uri.parse(vidAddress + mediumQueue.get(index));
                    vidView.setVideoURI(vidUri);
                    vidView.start();
                }

                current = mediumQueue;
            }
        });

        // High button onclick listener
        high.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!startflag) {
                    index = 0;
                    startflag = true;

                    vidUri = Uri.parse(vidAddress + highQueue.get(index));
                    vidView.setVideoURI(vidUri);
                    vidView.start();
                }

                current = highQueue;
            }
        });

        // A listener of video to detect video is completion or not
        vidView.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
            @Override
            public void onCompletion(MediaPlayer mp) {
                if (index >= lowQueue.size() - 1) {
                    vidView.pause();
                    startflag = false;
                }

                if (startflag) {
                    index++;
                    vidUri = Uri.parse(vidAddress + current.get(index));
                    vidView.setVideoURI(vidUri);
                    vidView.start();
                }
            }
        });
    }
}
