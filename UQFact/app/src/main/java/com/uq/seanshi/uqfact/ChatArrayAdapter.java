package com.uq.seanshi.uqfact;

/**
 * Created by seanshi on 9/5/17.
 */

import android.content.Context;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.iflytek.cloud.SpeechConstant;
import com.iflytek.cloud.SpeechSynthesizer;

import java.util.ArrayList;
import java.util.List;


class ChatArrayAdapter extends ArrayAdapter<ChatMessage> {

    private TextView chatText;
    private List<ChatMessage> chatMessageList = new ArrayList<ChatMessage>();
    private Context context;
    private SpeechSynthesizer mTts;

    @Override
    public void add(ChatMessage object) {
        chatMessageList.add(object);
        super.add(object);
    }

    public ChatArrayAdapter(Context context, int textViewResourceId, SpeechSynthesizer mTts) {
        super(context, textViewResourceId);
        this.context = context;
        this.mTts = mTts;
    }

    public int getCount() {
        return this.chatMessageList.size();
    }

    public ChatMessage getItem(int index) {
        return this.chatMessageList.get(index);
    }

    public View getView(int position, View convertView, ViewGroup parent) {
        final ChatMessage chatMessageObj = getItem(position);
        View row = convertView;
        LayoutInflater inflater = (LayoutInflater) this.getContext().getSystemService(Context.LAYOUT_INFLATER_SERVICE);
        if (chatMessageObj.left) {
            row = inflater.inflate(R.layout.left, parent, false);
        }else{
            if (chatMessageObj.wantTrain) {
                row = inflater.inflate(R.layout.right_train, parent, false);
                TextView notTrain = (TextView) row.findViewById(R.id.notTrain);
                TextView train = (TextView) row.findViewById(R.id.train);
                notTrain.setOnClickListener(new View.OnClickListener() {
                    @Override
                    public void onClick(View view) {
                        if (chatMessageObj.wantNationality) {
                            ((MainActivity) context).DomesticStudent();
                        } else {
                            ((MainActivity) context).NotSelfTrain();
                        }
                    }
                });
                train.setOnClickListener(new View.OnClickListener() {
                    @Override
                    public void onClick(View view) {
                        if (chatMessageObj.wantNationality) {
                            ((MainActivity) context).InternationalStudent();
                        } else {
                            ((MainActivity) context).YesSelfTrain();
                        }
                    }
                });
            } else {
                row = inflater.inflate(R.layout.right, parent, false);
            }
        }
        chatText = (TextView) row.findViewById(R.id.msgr);
        chatText.setText(chatMessageObj.message);
        chatText.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                mTts.stopSpeaking();
            }
        });
        return row;
    }

}
