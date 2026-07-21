"""Add logistics models (hubs, handlers, fleet vehicles, shipment logs)

Revision ID: 001_add_logistics_models
Revises: 
Create Date: 2026-04-16 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_add_logistics_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all new logistics tables and update existing tables"""
    
    # Create hubs table
    op.create_table(
        'hubs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(2), nullable=False),
        sa.Column('postal_code', sa.String(10), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('sorting_capacity', sa.Integer(), nullable=True),
        sa.Column('storage_capacity', sa.Integer(), nullable=True),
        sa.Column('operating_hours_start', sa.String(5), nullable=True),
        sa.Column('operating_hours_end', sa.String(5), nullable=True),
        sa.Column('manager_name', sa.String(255), nullable=True),
        sa.Column('manager_email', sa.String(255), nullable=True),
        sa.Column('manager_phone', sa.String(20), nullable=True),
        sa.Column('status', sa.Enum('active', 'maintenance', 'closed', 'pending', name='hubstatus'), nullable=False, server_default='active'),
        sa.Column('is_regional_hub', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_hub_id', sa.Integer(), nullable=True),
        sa.Column('total_capacity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('available_capacity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
    )
    op.create_index(op.f('ix_hubs_code'), 'hubs', ['code'], unique=True)
    op.create_index(op.f('ix_hubs_name'), 'hubs', ['name'], unique=True)
    op.create_index(op.f('ix_hubs_city'), 'hubs', ['city'])
    op.create_index(op.f('ix_hubs_created_at'), 'hubs', ['created_at'])
    
    # Create fleet_vehicles table
    op.create_table(
        'fleet_vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plate_number', sa.String(50), nullable=False),
        sa.Column('vin', sa.String(50), nullable=True),
        sa.Column('vehicle_type', sa.Enum('motorcycle', 'car', 'van', 'truck', 'cargo', name='vehicletype'), nullable=False),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(50), nullable=True),
        sa.Column('hub_id', sa.Integer(), nullable=False),
        sa.Column('current_driver_id', sa.Integer(), nullable=True),
        sa.Column('weight_capacity', sa.Float(), nullable=False),
        sa.Column('volume_capacity', sa.Float(), nullable=False),
        sa.Column('max_packages', sa.Integer(), nullable=False),
        sa.Column('current_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('current_packages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_latitude', sa.Float(), nullable=True),
        sa.Column('current_longitude', sa.Float(), nullable=True),
        sa.Column('last_location_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('available', 'in_use', 'maintenance', 'decommissioned', 'inactive', name='vehiclestatus'), nullable=False, server_default='available'),
        sa.Column('registration_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('insurance_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inspection_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mileage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('next_maintenance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fuel_type', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['hub_id'], ['hubs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plate_number'),
        sa.UniqueConstraint('vin'),
    )
    op.create_index(op.f('ix_fleet_vehicles_plate_number'), 'fleet_vehicles', ['plate_number'], unique=True)
    op.create_index(op.f('ix_fleet_vehicles_hub_id'), 'fleet_vehicles', ['hub_id'])
    op.create_index(op.f('ix_fleet_vehicles_created_at'), 'fleet_vehicles', ['created_at'])
    
    # Create handlers table
    op.create_table(
        'handlers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('handler_type', sa.Enum('warehouse_staff', 'driver', name='handlertype'), nullable=False),
        sa.Column('hub_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('active', 'on_leave', 'inactive', 'suspended', name='handlerstatus'), nullable=False, server_default='active'),
        sa.Column('license_number', sa.String(50), nullable=True),
        sa.Column('license_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('license_category', sa.String(10), nullable=True),
        sa.Column('employee_id', sa.String(50), nullable=True),
        sa.Column('hire_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('badge_number', sa.String(50), nullable=True),
        sa.Column('scanner_id', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hub_id'], ['hubs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('employee_id'),
        sa.UniqueConstraint('badge_number'),
    )
    op.create_index(op.f('ix_handlers_user_id'), 'handlers', ['user_id'], unique=True)
    op.create_index(op.f('ix_handlers_hub_id'), 'handlers', ['hub_id'])
    op.create_index(op.f('ix_handlers_email'), 'handlers', ['email'])
    op.create_index(op.f('ix_handlers_created_at'), 'handlers', ['created_at'])
    
    # Create shipment_logs table (audit trail)
    op.create_table(
        'shipment_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('tracking_number', sa.String(50), nullable=False),
        sa.Column('action', sa.Enum('order_received', 'payment_confirmed', 'scanned', 'sorted', 'dispatched', 'packed', 'pickup_started', 'picked_up', 'in_transit', 'at_hub', 'departed_hub', 'out_for_delivery', 'delivery_attempt', 'delivered', 'delivery_failed', 'returned', 'damaged', 'lost', 'manual_override', name='logaction'), nullable=False),
        sa.Column('previous_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=True),
        sa.Column('handler_id', sa.Integer(), nullable=True),
        sa.Column('handler_name', sa.String(255), nullable=True),
        sa.Column('hub_id', sa.Integer(), nullable=True),
        sa.Column('hub_name', sa.String(255), nullable=True),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('vehicle_plate', sa.String(50), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(500), nullable=True),
        sa.Column('barcode_scanned', sa.String(255), nullable=True),
        sa.Column('device_id', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('proof_image_url', sa.String(500), nullable=True),
        sa.Column('distance_from_destination', sa.Float(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_method', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['handler_id'], ['handlers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shipment_logs_shipment_id'), 'shipment_logs', ['shipment_id'])
    op.create_index(op.f('ix_shipment_logs_tracking_number'), 'shipment_logs', ['tracking_number'])
    op.create_index(op.f('ix_shipment_logs_action'), 'shipment_logs', ['action'])
    op.create_index(op.f('ix_shipment_logs_timestamp'), 'shipment_logs', ['timestamp'])
    op.create_index(op.f('ix_shipment_logs_created_at'), 'shipment_logs', ['created_at'])
    
    # Alter users table to add assigned_hub_id
    op.add_column('users', sa.Column('assigned_hub_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_assigned_hub_id'), 'users', ['assigned_hub_id'])
    
    # Alter shipments table to add logistics fields
    op.add_column('shipments', sa.Column('origin_hub_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('destination_hub_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('current_hub_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('assigned_handler_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('assigned_vehicle_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('shipments', sa.Column('delivery_proof_signature', sa.Text(), nullable=True))
    op.add_column('shipments', sa.Column('delivery_proof_photo', sa.String(500), nullable=True))
    op.add_column('shipments', sa.Column('signature_required', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('shipments', sa.Column('last_location_update', sa.DateTime(), nullable=True))
    
    # Create foreign key constraints for shipments
    op.create_foreign_key('fk_shipments_origin_hub_id', 'shipments', 'hubs', ['origin_hub_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_shipments_destination_hub_id', 'shipments', 'hubs', ['destination_hub_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_shipments_current_hub_id', 'shipments', 'hubs', ['current_hub_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_shipments_assigned_handler_id', 'shipments', 'handlers', ['assigned_handler_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_shipments_assigned_vehicle_id', 'shipments', 'fleet_vehicles', ['assigned_vehicle_id'], ['id'], ondelete='SET NULL')
    
    op.create_index(op.f('ix_shipments_origin_hub_id'), 'shipments', ['origin_hub_id'])
    op.create_index(op.f('ix_shipments_destination_hub_id'), 'shipments', ['destination_hub_id'])
    op.create_index(op.f('ix_shipments_current_hub_id'), 'shipments', ['current_hub_id'])


def downgrade() -> None:
    """Downgrade: Remove logistics tables and shipment columns"""
    
    # Drop indexes on shipments
    op.drop_index(op.f('ix_shipments_current_hub_id'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_destination_hub_id'), table_name='shipments')
    op.drop_index(op.f('ix_shipments_origin_hub_id'), table_name='shipments')
    
    # Drop foreign keys from shipments
    op.drop_constraint('fk_shipments_assigned_vehicle_id', 'shipments', type_='foreignkey')
    op.drop_constraint('fk_shipments_assigned_handler_id', 'shipments', type_='foreignkey')
    op.drop_constraint('fk_shipments_current_hub_id', 'shipments', type_='foreignkey')
    op.drop_constraint('fk_shipments_destination_hub_id', 'shipments', type_='foreignkey')
    op.drop_constraint('fk_shipments_origin_hub_id', 'shipments', type_='foreignkey')
    
    # Drop shipments columns
    op.drop_column('shipments', 'last_location_update')
    op.drop_column('shipments', 'signature_required')
    op.drop_column('shipments', 'delivery_proof_photo')
    op.drop_column('shipments', 'delivery_proof_signature')
    op.drop_column('shipments', 'is_locked')
    op.drop_column('shipments', 'assigned_vehicle_id')
    op.drop_column('shipments', 'assigned_handler_id')
    op.drop_column('shipments', 'current_hub_id')
    op.drop_column('shipments', 'destination_hub_id')
    op.drop_column('shipments', 'origin_hub_id')
    
    # Drop users index and column
    op.drop_index(op.f('ix_users_assigned_hub_id'), table_name='users')
    op.drop_column('users', 'assigned_hub_id')
    
    # Drop shipment_logs table
    op.drop_table('shipment_logs')
    
    # Drop handlers table
    op.drop_table('handlers')
    
    # Drop fleet_vehicles table
    op.drop_table('fleet_vehicles')
    
    # Drop hubs table
    op.drop_table('hubs')
