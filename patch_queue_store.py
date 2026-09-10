from pathlib import Path

path = Path("app/src/main/java/com/serhat/autosub/queue/QueueStore.java")
text = path.read_text(encoding="utf-8")

anchor = '    private static final String TABLE = "queue_items";\n'
insert = '''    private static final String TABLE = "queue_items";\n    // Keep large subtitle payloads out of the main CursorWindow. Android CursorWindow\n    // has a per-row size limit, while subtitles_json can grow to several megabytes\n    // for long videos (especially with per-word timing and translations).\n    private static final int SUBTITLE_JSON_CHUNK_CHARS = 64 * 1024;\n    private static final String[] ITEM_COLUMNS = new String[]{\n            "id", "video_uri", "display_name", "status", "progress",\n            "output_path", "srt_path", "vtt_path", "soft_video_path", "hard_video_path",\n            "message", "preview_text",\n            "translation_source_language", "translation_target_language", "translation_status",\n            "shorts_video", "use_vad",\n            "shorts_caption_x", "shorts_caption_y", "shorts_caption_scale",\n            "subtitle_caption_x", "subtitle_caption_y", "subtitle_caption_scale",\n            "subtitle_caption_adjusted", "thumbnail_path", "audio_path"\n    };\n'''
if anchor not in text:
    raise SystemExit("QueueStore TABLE anchor not found")
text = text.replace(anchor, insert, 1)

old_query = 'try (Cursor cursor = getReadableDatabase().query(TABLE, null, null, null, null, null, "created_at DESC")) {'
new_query = 'try (Cursor cursor = getReadableDatabase().query(TABLE, ITEM_COLUMNS, null, null, null, null, "created_at DESC")) {'
if old_query not in text:
    raise SystemExit("QueueStore getItems query anchor not found")
text = text.replace(old_query, new_query, 1)

old_read = 'item.setSubtitles(subtitlesFromJson(cursor.getString(cursor.getColumnIndexOrThrow("subtitles_json"))));'
new_read = 'item.setSubtitles(loadSubtitlesChunked(id));'
if old_read not in text:
    raise SystemExit("QueueStore subtitles_json read anchor not found")
text = text.replace(old_read, new_read, 1)

helper_anchor = '    private float getOptionalFloat(Cursor cursor, String columnName, float defaultValue) {'
helper = '''    /**\n     * Reads subtitles_json in small TEXT chunks so no CursorWindow row ever contains\n     * the full subtitle payload. SQLite substr(TEXT, start, length) uses 1-based\n     * character offsets, which keeps UTF-8/CJK text boundaries intact.\n     *\n     * The returned JSON is passed through the original subtitlesFromJson method, so\n     * the in-memory QueueItem contents and all downstream behavior remain unchanged.\n     */\n    private List<SubtitleGenerator.SubtitleEntry> loadSubtitlesChunked(long id) {\n        StringBuilder json = new StringBuilder();\n        int offset = 1;\n        SQLiteDatabase db = getReadableDatabase();\n\n        while (true) {\n            String chunk;\n            try (Cursor cursor = db.rawQuery(\n                    "SELECT substr(subtitles_json, ?, ?) FROM " + TABLE + " WHERE id = ?",\n                    new String[]{String.valueOf(offset),\n                            String.valueOf(SUBTITLE_JSON_CHUNK_CHARS),\n                            String.valueOf(id)})) {\n                if (!cursor.moveToFirst() || cursor.isNull(0)) {\n                    break;\n                }\n                chunk = cursor.getString(0);\n            }\n\n            if (chunk == null || chunk.isEmpty()) {\n                break;\n            }\n\n            json.append(chunk);\n            if (chunk.length() < SUBTITLE_JSON_CHUNK_CHARS) {\n                break;\n            }\n            offset += SUBTITLE_JSON_CHUNK_CHARS;\n        }\n\n        return subtitlesFromJson(json.toString());\n    }\n\n'''
if helper_anchor not in text:
    raise SystemExit("QueueStore helper insertion anchor not found")
text = text.replace(helper_anchor, helper + helper_anchor, 1)

# Guard against accidentally leaving the dangerous full-row query/read in place.
if 'query(TABLE, null, null, null, null, null, "created_at DESC")' in text:
    raise SystemExit("Unsafe SELECT-all query still present")
if 'getColumnIndexOrThrow("subtitles_json")' in text:
    raise SystemExit("Unsafe direct subtitles_json CursorWindow read still present")

path.write_text(text, encoding="utf-8")
print("QueueStore large-row fix applied successfully")
