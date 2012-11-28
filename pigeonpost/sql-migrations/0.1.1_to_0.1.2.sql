BEGIN;
ALTER TABLE pigeonpost_pigeon DROP CONSTRAINT "pigeonpost_pigeon_source_content_type_id_source_id_key";
ALTER TABLE pigeonpost_pigeon ADD COLUMN "send_to_id" integer;
ALTER TABLE pigeonpost_pigeon ADD COLUMN "send_to_method" text;
COMMIT;
