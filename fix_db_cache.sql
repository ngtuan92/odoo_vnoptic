-- Clear action cache for vnoptic_product
DELETE FROM ir_act_window WHERE res_model = 'product.creation.wizard';

-- Clear view cache
DELETE FROM ir_ui_view_cache;

-- Clear menu cache
DELETE FROM ir_ui_menu WHERE action LIKE '%wizard%';

-- Rebuild menu
-- You'll need to reinstall/upgrade the module after this
