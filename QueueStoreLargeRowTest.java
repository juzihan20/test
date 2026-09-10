package com.serhat.autosub.queue;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;

import android.content.ContentValues;
import android.content.Context;
import android.database.sqlite.SQLiteDatabase;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.List;

@RunWith(AndroidJUnit4.class)
public class QueueStoreLargeRowTest {
    private Context context;
    private QueueStore store;

    @Before
    public void setUp() {
        context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase("autosub_queue.db");
        store = new QueueStore(context);
    }

    @After
    public void tearDown() {
        if (store != null) {
            store.close();
        }
        context.deleteDatabase("autosub_queue.db");
    }

    @Test
    public void getItems_readsSubtitleJsonLargerThanCursorWindow() throws Exception {
        // Deliberately exceed the typical Android CursorWindow row capacity.
        StringBuilder builder = new StringBuilder(5 * 1024 * 1024);
        for (int i = 0; i < 655360; i++) {
            builder.append("字幕TEST");
        }
        String hugeText = builder.toString();

        JSONObject subtitle = new JSONObject();
        subtitle.put("number", 1);
        subtitle.put("start", "00:00:00,000");
        subtitle.put("end", "00:00:05,000");
        subtitle.put("text", hugeText);
        subtitle.put("translationText", "中文翻译");
        subtitle.put("words", new JSONArray());
        JSONArray subtitles = new JSONArray();
        subtitles.put(subtitle);

        ContentValues values = new ContentValues();
        values.put("video_uri", "content://autosub-test/video.mp4");
        values.put("display_name", "large-row-test.mp4");
        values.put("status", QueueItem.Status.COMPLETED.name());
        values.put("progress", 100);
        values.put("preview_text", "preview");
        values.put("subtitles_json", subtitles.toString());
        values.put("created_at", System.currentTimeMillis());

        SQLiteDatabase db = store.getWritableDatabase();
        long id = db.insertOrThrow("queue_items", null, values);

        List<QueueItem> items = store.getItems();
        assertFalse(items.isEmpty());
        assertEquals(id, items.get(0).getId());
        assertEquals(1, items.get(0).getSubtitles().size());
        assertEquals(hugeText, items.get(0).getSubtitles().get(0).getText());
        assertEquals("中文翻译", items.get(0).getSubtitles().get(0).getTranslationText());
    }
}
