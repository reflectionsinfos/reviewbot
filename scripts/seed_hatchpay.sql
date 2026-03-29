-- ============================================================
-- Hatch Pay project seed
-- Copies delivery + technical checklist data from NeUMoney (project_id=2)
-- Safe to re-run: project insert uses ON CONFLICT DO NOTHING
-- ============================================================
DO $$
DECLARE
  admin_id    INT;
  rvwr_id     INT;
  proj_id     INT;
  del_cl_id   INT;
  tec_cl_id   INT;
  del_rv_id   INT;
  tec_rv_id   INT;
  del_rpt_id  INT;
  tec_rpt_id  INT;
  item        RECORD;
  resp        RECORD;
  new_item_id INT;
BEGIN
  SELECT id INTO admin_id FROM users WHERE email = 'admin@reviewbot.com';
  SELECT id INTO rvwr_id  FROM users WHERE email = 'reviewer@reviewbot.com';

  -- Skip if already exists
  IF EXISTS (SELECT 1 FROM projects WHERE name = 'Hatch Pay') THEN
    RAISE NOTICE 'Hatch Pay already exists, skipping.';
    RETURN;
  END IF;

  -- 1. Project
  INSERT INTO projects (name, domain, status, owner_id, created_at)
  VALUES ('Hatch Pay', 'fintech', 'active', admin_id, NOW())
  RETURNING id INTO proj_id;
  RAISE NOTICE 'Created project id=%', proj_id;

  -- 2. Delivery checklist + items (copy from checklist 5)
  INSERT INTO checklists (name, type, version, project_id, is_global, created_at)
  VALUES ('Hatch Pay — Delivery Checklist', 'delivery', '1.0', proj_id, FALSE, NOW())
  RETURNING id INTO del_cl_id;

  FOR item IN SELECT * FROM checklist_items WHERE checklist_id = 5 ORDER BY "order" LOOP
    INSERT INTO checklist_items
      (checklist_id, item_code, area, question, category, weight, is_review_mandatory, expected_evidence, "order", created_at)
    VALUES
      (del_cl_id, item.item_code, item.area, item.question, item.category,
       item.weight, item.is_review_mandatory, item.expected_evidence, item."order", NOW());
  END LOOP;

  -- 3. Technical checklist + items (copy from checklist 6)
  INSERT INTO checklists (name, type, version, project_id, is_global, created_at)
  VALUES ('Hatch Pay — Technical Checklist', 'technical', '1.0', proj_id, FALSE, NOW())
  RETURNING id INTO tec_cl_id;

  FOR item IN SELECT * FROM checklist_items WHERE checklist_id = 6 ORDER BY "order" LOOP
    INSERT INTO checklist_items
      (checklist_id, item_code, area, question, category, weight, is_review_mandatory, expected_evidence, "order", created_at)
    VALUES
      (tec_cl_id, item.item_code, item.area, item.question, item.category,
       item.weight, item.is_review_mandatory, item.expected_evidence, item."order", NOW());
  END LOOP;

  -- 4. Delivery review + responses (copy RAG from NeUMoney review 3)
  INSERT INTO reviews
    (project_id, checklist_id, title, status, conducted_by, voice_enabled, review_date, created_at, completed_at)
  VALUES
    (proj_id, del_cl_id, 'Hatch Pay Delivery Review', 'completed', rvwr_id, FALSE, NOW(), NOW(), NOW())
  RETURNING id INTO del_rv_id;

  FOR resp IN
    SELECT rr.answer, rr.comments, rr.rag_status, ci."order"
    FROM review_responses rr
    JOIN checklist_items ci ON ci.id = rr.checklist_item_id
    WHERE rr.review_id = 3
    ORDER BY ci."order"
  LOOP
    INSERT INTO review_responses (review_id, checklist_item_id, answer, comments, rag_status, created_at)
    SELECT del_rv_id, id, resp.answer, resp.comments, resp.rag_status, NOW()
    FROM checklist_items
    WHERE checklist_id = del_cl_id AND "order" = resp."order";
  END LOOP;

  INSERT INTO reports
    (review_id, summary, overall_rag_status, compliance_score,
     areas_followed, gaps_identified, recommendations, action_items,
     approval_status, requires_approval, created_at)
  SELECT
    del_rv_id, summary, overall_rag_status, compliance_score,
    areas_followed, gaps_identified, recommendations, action_items,
    'pending', TRUE, NOW()
  FROM reports WHERE review_id = 3
  RETURNING id INTO del_rpt_id;

  -- 5. Technical review + responses (copy RAG from NeUMoney review 4)
  INSERT INTO reviews
    (project_id, checklist_id, title, status, conducted_by, voice_enabled, review_date, created_at, completed_at)
  VALUES
    (proj_id, tec_cl_id, 'Hatch Pay Technical Review', 'completed', rvwr_id, FALSE, NOW(), NOW(), NOW())
  RETURNING id INTO tec_rv_id;

  FOR resp IN
    SELECT rr.answer, rr.comments, rr.rag_status, ci."order"
    FROM review_responses rr
    JOIN checklist_items ci ON ci.id = rr.checklist_item_id
    WHERE rr.review_id = 4
    ORDER BY ci."order"
  LOOP
    INSERT INTO review_responses (review_id, checklist_item_id, answer, comments, rag_status, created_at)
    SELECT tec_rv_id, id, resp.answer, resp.comments, resp.rag_status, NOW()
    FROM checklist_items
    WHERE checklist_id = tec_cl_id AND "order" = resp."order";
  END LOOP;

  INSERT INTO reports
    (review_id, summary, overall_rag_status, compliance_score,
     areas_followed, gaps_identified, recommendations, action_items,
     approval_status, requires_approval, created_at)
  SELECT
    tec_rv_id, summary, overall_rag_status, compliance_score,
    areas_followed, gaps_identified, recommendations, action_items,
    'pending', TRUE, NOW()
  FROM reports WHERE review_id = 4
  RETURNING id INTO tec_rpt_id;

  RAISE NOTICE 'Hatch Pay inserted: project=% del_cl=% tec_cl=% del_rv=% tec_rv=% del_rpt=% tec_rpt=%',
    proj_id, del_cl_id, tec_cl_id, del_rv_id, tec_rv_id, del_rpt_id, tec_rpt_id;
END $$;

