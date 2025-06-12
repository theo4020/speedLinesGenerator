import bpy
import bmesh
import mathutils
from mathutils import Vector
import random
import math

bl_info = {
    "name": "Animated Speed Lines Generator",
    "author": "Assistant",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Speed Lines",
    "description": "Generate animated 3D speed lines in a zone",
    "category": "Mesh",
}

class SPEEDLINES_OT_speed_preset(bpy.types.Operator):
    """Apply Speed Preset"""
    bl_idname = "speedlines.speed_preset"
    bl_label = "Speed Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_type: bpy.props.EnumProperty(
        items=[
            ('SLOW', "Slow Flow", "Gentle, slow-moving lines"),
            ('FAST', "Fast Flow", "Quick-moving lines"),
            ('BULLET_TIME', "Bullet Time", "Ultra-fast speed lines")
        ]
    )
    
    def execute(self, context):
        props = context.scene.speedlines_props
        
        if self.preset_type == 'SLOW':
            props.speed_units_per_second = 2.0
            props.animation_speed = 0.5
            props.animation_duration = 800.0  # Very long for slow random spawning
            props.cycle_length = 2.0
            props.line_count = 250
            props.spawn_randomness = 0.7
        elif self.preset_type == 'FAST':
            props.speed_units_per_second = 15.0
            props.animation_speed = 2.0
            props.animation_duration = 400.0
            props.cycle_length = 1.5
            props.line_count = 300
            props.spawn_randomness = 0.8
        elif self.preset_type == 'BULLET_TIME':
            props.speed_units_per_second = 40.0
            props.animation_speed = 5.0
            props.animation_duration = 200.0
            props.cycle_length = 1.0
            props.line_count = 200
            props.spawn_randomness = 0.9
        
        self.report({'INFO'}, f"Applied {self.preset_type.replace('_', ' ').title()} preset - random forward flow!")
        return {'FINISHED'}

class SPEEDLINES_OT_continuous_flow(bpy.types.Operator):
    """Setup Perfect Continuous Flow"""
    bl_idname = "speedlines.continuous_flow"
    bl_label = "Continuous Flow Setup"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.speedlines_props
        
        # Optimal settings for permanent forward motion with random spawning
        props.animation_duration = 600.0  # Longer duration for extended spawning
        props.animation_speed = 1.0
        props.cycle_length = 1.0  # Not really used in new system
        props.spawn_randomness = 0.9  # Very random spawning
        props.line_count = 300  # More lines for continuous random effect
        props.pattern = 'PARALLEL'
        props.line_type = 'TAPERED'
        props.flow_direction = (1.0, 0.0, 0.0)
        props.line_length = 2.0  # Shorter lines for denser effect
        props.randomness = 0.2  # Some position randomness
        
        self.report({'INFO'}, "Set up random spawning permanent forward flow!")
        return {'FINISHED'}

class SPEEDLINES_OT_generate(bpy.types.Operator):
    """Generate Animated Speed Lines"""
    bl_idname = "speedlines.generate"
    bl_label = "Generate Speed Lines"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            scene = context.scene
            props = scene.speedlines_props
            
            # Clear existing speed lines if replace is enabled
            if props.replace_existing:
                self.clear_speed_lines()
            
            # Create speed lines collection
            collection = self.create_collection()
            
            # Create speed lines
            self.generate_speed_lines(props, collection)
            
            # Create control object
            self.create_control_object(props, collection)
            
            self.report({'INFO'}, f"Generated {props.line_count} animated speed lines!")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error generating speed lines: {str(e)}")
            return {'CANCELLED'}
    
    def clear_speed_lines(self):
        """Remove existing speed lines"""
        # Remove collection and all its objects
        if "SpeedLines" in bpy.data.collections:
            collection = bpy.data.collections["SpeedLines"]
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
    
    def create_collection(self):
        """Create or get the speed lines collection"""
        if "SpeedLines" not in bpy.data.collections:
            collection = bpy.data.collections.new("SpeedLines")
            bpy.context.scene.collection.children.link(collection)
        else:
            collection = bpy.data.collections["SpeedLines"]
        return collection
    
    def create_control_object(self, props, collection):
        """Create a control object for animation properties"""
        # Create empty object for controls
        bpy.ops.object.empty_add(type='SPHERE', location=props.zone_center)
        control_obj = bpy.context.active_object
        control_obj.name = "SpeedLines_Controller"
        control_obj.empty_display_size = 0.5
        
        # Move to collection safely
        if control_obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(control_obj)
        collection.objects.link(control_obj)
        
        # Add custom properties
        control_obj["speed_units_per_second"] = props.speed_units_per_second
        control_obj["animation_speed"] = props.animation_speed
        control_obj["animation_duration"] = props.animation_duration
        control_obj["flow_direction_x"] = props.flow_direction[0]
        control_obj["flow_direction_y"] = props.flow_direction[1]
        control_obj["flow_direction_z"] = props.flow_direction[2]
        control_obj["cycle_length"] = props.cycle_length
        control_obj["spawn_randomness"] = props.spawn_randomness
        
        # Add property UI settings
        control_obj.id_properties_ui("speed_units_per_second").update(min=0.1, max=200.0)
        control_obj.id_properties_ui("animation_speed").update(min=0.1, max=50.0)
        control_obj.id_properties_ui("animation_duration").update(min=60.0, max=2000.0)
        control_obj.id_properties_ui("flow_direction_x").update(min=-1.0, max=1.0)
        control_obj.id_properties_ui("flow_direction_y").update(min=-1.0, max=1.0)
        control_obj.id_properties_ui("flow_direction_z").update(min=-1.0, max=1.0)
        control_obj.id_properties_ui("cycle_length").update(min=1.0, max=50.0)
        control_obj.id_properties_ui("spawn_randomness").update(min=0.0, max=1.0)
        
        return control_obj
    
    def generate_speed_lines(self, props, collection):
        """Generate the speed lines based on properties"""
        for i in range(props.line_count):
            self.create_animated_speed_line(props, collection, i)
    
    def create_animated_speed_line(self, props, collection, index):
        """Create a single animated speed line"""
        # Create mesh and object
        mesh = bpy.data.meshes.new(f"SpeedLine_{index}")
        obj = bpy.data.objects.new(f"SpeedLine_{index}", mesh)
        collection.objects.link(obj)
        
        # Create bmesh
        bm = bmesh.new()
        
        # Calculate line properties
        position, flow_direction, line_data = self.calculate_line_properties(props, index)
        
        # Create line geometry in standard orientation (along X-axis)
        standard_start = Vector((-props.line_length / 2, 0, 0))
        standard_end = Vector((props.line_length / 2, 0, 0))
        
        # Create line geometry
        if props.line_type == 'SIMPLE':
            self.create_simple_line(bm, standard_start, standard_end, props)
        elif props.line_type == 'TAPERED':
            self.create_tapered_line(bm, standard_start, standard_end, props)
        elif props.line_type == 'TUBE':
            self.create_tube_line(bm, standard_start, standard_end, props)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Position and orient the object
        obj.location = position
        
        # Rotate object to point in flow direction
        if flow_direction.length > 0.001:
            # Calculate rotation to align X-axis with flow direction
            x_axis = Vector((1, 0, 0))
            rotation_quat = x_axis.rotation_difference(flow_direction)
            obj.rotation_euler = rotation_quat.to_euler()
        
        # Store line data for animation
        obj["base_position"] = position
        obj["flow_direction"] = flow_direction
        obj["cycle_offset"] = line_data["cycle_offset"]
        obj["spawn_delay"] = line_data["spawn_delay"]
        
        # Apply material
        self.apply_speed_line_material(obj, props)
        
        # Add animation
        self.add_line_animation(obj, props)
    
    def calculate_line_properties(self, props, index):
        """Calculate properties for a speed line"""
        zone_center = Vector(props.zone_center)
        zone_size = Vector(props.zone_size)
        flow_direction = Vector(props.flow_direction).normalized()
        
        if props.pattern == 'PARALLEL':
            # Create perpendicular vectors for line distribution
            if abs(flow_direction.z) < 0.9:
                perpendicular1 = Vector((-flow_direction.y, flow_direction.x, 0)).normalized()
                perpendicular2 = flow_direction.cross(perpendicular1).normalized()
            else:
                perpendicular1 = Vector((1, 0, 0))
                perpendicular2 = Vector((0, 1, 0))
            
            # Distribute lines across the cross-section
            grid_size = int(math.sqrt(props.line_count))
            if grid_size == 0:
                grid_size = 1
            row = index // grid_size
            col = index % grid_size
            
            # Calculate position within the zone cross-section
            u = (row / max(1, grid_size - 1) - 0.5) if grid_size > 1 else 0
            v = (col / max(1, grid_size - 1) - 0.5) if grid_size > 1 else 0
            
            # Add randomness
            u += random.uniform(-props.randomness, props.randomness) * 0.5
            v += random.uniform(-props.randomness, props.randomness) * 0.5
            
            # Position in zone cross-section
            position = (zone_center + 
                       perpendicular1 * u * zone_size.length * 0.7 +
                       perpendicular2 * v * zone_size.length * 0.7)
            
            # Flow direction stays the same for parallel
            line_flow_direction = flow_direction.copy()
            
        elif props.pattern == 'RADIAL':
            # Radial pattern from center
            angle = (index / props.line_count) * 2 * math.pi
            angle += random.uniform(-props.randomness, props.randomness)
            
            direction = Vector((math.cos(angle), math.sin(angle), 0))
            
            # Position at inner radius
            position = zone_center + direction * props.min_distance
            
            # Flow direction is radial outward
            line_flow_direction = direction.copy()
            
        elif props.pattern == 'RANDOM':
            # Random placement within zone
            if abs(flow_direction.z) < 0.9:
                perpendicular1 = Vector((-flow_direction.y, flow_direction.x, 0)).normalized()
                perpendicular2 = flow_direction.cross(perpendicular1).normalized()
            else:
                perpendicular1 = Vector((1, 0, 0))
                perpendicular2 = Vector((0, 1, 0))
            
            # Random position
            u = random.uniform(-1, 1)
            v = random.uniform(-1, 1)
            
            position = (zone_center + 
                       perpendicular1 * u * zone_size.length * 0.4 +
                       perpendicular2 * v * zone_size.length * 0.4)
            
            # Add slight random variation to flow direction
            line_flow_direction = flow_direction.copy()
            line_flow_direction.x += random.uniform(-props.randomness * 0.3, props.randomness * 0.3)
            line_flow_direction.y += random.uniform(-props.randomness * 0.3, props.randomness * 0.3)
            line_flow_direction.z += random.uniform(-props.randomness * 0.1, props.randomness * 0.1)
            line_flow_direction.normalize()
        
        # Store additional data for animation - random spawning over time
        line_data = {
            "cycle_offset": random.uniform(0, 1),
            "spawn_delay": random.uniform(0, props.animation_duration * 2)  # Random spawn across extended time
        }
        
        return position, line_flow_direction, line_data
    
    def create_simple_line(self, bm, start_pos, end_pos, props):
        """Create a simple line"""
        v1 = bm.verts.new(start_pos)
        v2 = bm.verts.new(end_pos)
        bm.edges.new([v1, v2])
    
    def create_tapered_line(self, bm, start_pos, end_pos, props):
        """Create a tapered quad line (oriented along X-axis)"""
        # Create tapered line along X-axis (from start_pos to end_pos)
        length = (end_pos - start_pos).length
        width = props.line_width
        
        # Create quad vertices for tapered line
        v1 = bm.verts.new((start_pos.x, -width, 0))      # Start bottom
        v2 = bm.verts.new((start_pos.x, width, 0))       # Start top  
        v3 = bm.verts.new((end_pos.x, width * props.taper_factor, 0))    # End top (tapered)
        v4 = bm.verts.new((end_pos.x, -width * props.taper_factor, 0))   # End bottom (tapered)
        
        # Create face
        bm.faces.new([v1, v2, v3, v4])
    
    def create_tube_line(self, bm, start_pos, end_pos, props):
        """Create a cylindrical tube line (oriented along X-axis)"""
        length = (end_pos - start_pos).length
        
        # Create cylinder along X-axis
        bmesh.ops.create_cone(bm, 
                             cap_ends=True,
                             cap_tris=False,
                             segments=8,
                             diameter1=props.line_width,
                             diameter2=props.line_width * props.taper_factor,
                             depth=length)
        
        # The cone is created along Z-axis, rotate it to X-axis
        bmesh.ops.rotate(bm, 
                        cent=(0, 0, 0),
                        matrix=mathutils.Matrix.Rotation(math.radians(90), 3, 'Y'),
                        verts=bm.verts)
        
        # Move to correct position along X-axis
        center_x = (start_pos.x + end_pos.x) / 2
        bmesh.ops.translate(bm,
                           vec=(center_x, 0, 0),
                           verts=bm.verts)
    
    def apply_speed_line_material(self, obj, props):
        """Apply or create material for speed lines"""
        mat_name = "SpeedLine_Material"
        
        try:
            if mat_name not in bpy.data.materials:
                # Create new material
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                
                # Clear default nodes
                mat.node_tree.nodes.clear()
                
                # Create emission shader
                emission = mat.node_tree.nodes.new(type='ShaderNodeEmission')
                emission.location = (0, 0)
                emission.inputs['Strength'].default_value = props.emission_strength
                emission.inputs['Color'].default_value = (*props.line_color, 1.0)
                
                # Create output
                output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                output.location = (200, 0)
                
                # Link nodes
                mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
                
                # Enable transparency if needed
                if props.use_transparency:
                    mat.blend_method = 'ALPHA'
            else:
                mat = bpy.data.materials[mat_name]
            
            # Apply material
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat
                
        except Exception as e:
            print(f"Warning: Could not apply material to {obj.name}: {e}")
    
    def add_line_animation(self, obj, props):
        """Add permanent forward motion with random spawning"""
        try:
            # Get the flow direction from the stored object data
            flow_direction = Vector(obj.get("flow_direction", (1, 0, 0))).normalized()
            base_position = Vector(obj.get("base_position", (0, 0, 0)))
            spawn_delay = obj.get("spawn_delay", 0)
            
            zone_center = Vector(props.zone_center)
            zone_size = Vector(props.zone_size)
            
            # Calculate travel distance - much longer for continuous flow
            abs_flow = [abs(flow_direction.x), abs(flow_direction.y), abs(flow_direction.z)]
            main_axis = abs_flow.index(max(abs_flow))
            
            # Extended travel distance for long journey
            extended_distance = zone_size[main_axis] + props.line_length * 8
            
            # Calculate spawn point (far behind the zone)
            spawn_offset = -flow_direction * (zone_size[main_axis] / 2 + props.line_length * 4)
            spawn_position = base_position + spawn_offset
            
            # Calculate exit point (far past the zone)  
            exit_offset = flow_direction * (zone_size[main_axis] / 2 + props.line_length * 4)
            exit_position = base_position + exit_offset
            
            # Animation timing for permanent motion
            travel_frames = int(props.animation_duration / props.animation_speed)
            
            # Random spawn time within the animation range
            max_spawn_delay = int(props.spawn_randomness * travel_frames)
            random_spawn_delay = random.randint(0, max_spawn_delay)
            
            # Starting frame with random spawn delay
            start_frame = 1 + int(spawn_delay) + random_spawn_delay
            end_frame = start_frame + travel_frames
            
            # Clear existing animation
            obj.animation_data_clear()
            
            # PERMANENT FORWARD MOTION - NO CYCLING BACK
            # Hide at start (before spawn)
            bpy.context.scene.frame_set(1)
            obj.hide_viewport = True
            obj.hide_render = True
            obj.location = spawn_position
            obj.keyframe_insert(data_path="hide_viewport")
            obj.keyframe_insert(data_path="hide_render")
            obj.keyframe_insert(data_path="location")
            
            # Show when spawning
            bpy.context.scene.frame_set(start_frame)
            obj.hide_viewport = False
            obj.hide_render = False
            obj.location = spawn_position
            obj.keyframe_insert(data_path="hide_viewport")
            obj.keyframe_insert(data_path="hide_render")
            obj.keyframe_insert(data_path="location")
            
            # Move to exit position
            bpy.context.scene.frame_set(end_frame)
            obj.location = exit_position
            obj.hide_viewport = False
            obj.hide_render = False
            obj.keyframe_insert(data_path="location")
            obj.keyframe_insert(data_path="hide_viewport")
            obj.keyframe_insert(data_path="hide_render")
            
            # Hide after exiting (optional - keeps scene clean)
            bpy.context.scene.frame_set(end_frame + 10)
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport")
            obj.keyframe_insert(data_path="hide_render")
            
            # Set interpolation for smooth motion
            if obj.animation_data and obj.animation_data.action:
                for fcurve in obj.animation_data.action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        if "location" in fcurve.data_path:
                            keyframe.interpolation = 'LINEAR'
                        else:  # Hide/show keyframes
                            keyframe.interpolation = 'CONSTANT'
            
            # NO CYCLE MODIFIER - lines just move forward once and stay gone
                        
        except Exception as e:
            print(f"Warning: Could not add animation to {obj.name}: {e}")

class SpeedLinesProperties(bpy.types.PropertyGroup):
    """Properties for animated speed lines generation"""
    
    # Zone properties
    zone_center: bpy.props.FloatVectorProperty(
        name="Zone Center",
        description="Center of the speed lines zone",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION'
    )
    
    zone_size: bpy.props.FloatVectorProperty(
        name="Zone Size",
        description="Size of the speed lines zone",
        default=(10.0, 10.0, 5.0),
        min=0.1
    )
    
    # Line properties
    line_count: bpy.props.IntProperty(
        name="Line Count",
        description="Number of speed lines to generate (more = denser random spawning)",
        default=250,
        min=1,
        max=2000
    )
    
    line_length: bpy.props.FloatProperty(
        name="Line Length",
        description="Base length of speed lines",
        default=3.0,
        min=0.1
    )
    
    line_width: bpy.props.FloatProperty(
        name="Line Width",
        description="Width of speed lines",
        default=0.05,
        min=0.001
    )
    
    line_type: bpy.props.EnumProperty(
        name="Line Type",
        description="Type of speed lines",
        items=[
            ('SIMPLE', "Simple", "Simple line edges"),
            ('TAPERED', "Tapered", "Tapered quad lines"),
            ('TUBE', "Tube", "3D cylindrical tubes")
        ],
        default='TAPERED'
    )
    
    # Animation properties
    speed_units_per_second: bpy.props.FloatProperty(
        name="Speed (Units/Sec)",
        description="How many Blender units lines travel per second",
        default=10.0,
        min=0.1,
        max=200.0
    )
    
    animation_speed: bpy.props.FloatProperty(
        name="Speed Multiplier",
        description="Multiplier for animation speed (higher = faster)",
        default=1.0,
        min=0.1,
        max=10.0
    )
    
    animation_duration: bpy.props.FloatProperty(
        name="Animation Duration",
        description="Base duration for lines to cross zone (frames) - longer = more random spawning time",
        default=400.0,
        min=60.0,
        max=2000.0
    )
    
    flow_direction: bpy.props.FloatVectorProperty(
        name="Flow Direction",
        description="Direction lines flow through the zone",
        default=(1.0, 0.0, 0.0),
        subtype='DIRECTION'
    )
    
    cycle_length: bpy.props.FloatProperty(
        name="Spawn Stagger",
        description="Time spacing between line spawns for continuous flow (frames)",
        default=5.0,
        min=1.0,
        max=50.0
    )
    
    spawn_randomness: bpy.props.FloatProperty(
        name="Spawn Randomness",
        description="How randomly spread out line spawning is (0 = regular, 1 = very random)",
        default=0.8,
        min=0.0,
        max=1.0
    )
    
    # Pattern properties
    pattern: bpy.props.EnumProperty(
        name="Pattern",
        description="Speed lines pattern",
        items=[
            ('RADIAL', "Radial", "Radial pattern from center"),
            ('PARALLEL', "Parallel", "Parallel flowing lines"),
            ('RANDOM', "Random", "Random placement and direction")
        ],
        default='PARALLEL'
    )
    
    spacing: bpy.props.FloatProperty(
        name="Spacing",
        description="Spacing between parallel lines",
        default=0.3,
        min=0.01
    )
    
    min_distance: bpy.props.FloatProperty(
        name="Min Distance",
        description="Minimum distance from center (radial pattern)",
        default=1.0,
        min=0.0
    )
    
    # Variation properties
    randomness: bpy.props.FloatProperty(
        name="Randomness",
        description="Amount of randomness in positioning",
        default=0.2,
        min=0.0,
        max=1.0
    )
    
    length_variation: bpy.props.FloatProperty(
        name="Length Variation",
        description="Random variation in line length",
        default=0.5,
        min=0.0
    )
    
    taper_factor: bpy.props.FloatProperty(
        name="Taper Factor",
        description="How much lines taper (0 = no taper, 1 = full taper)",
        default=0.1,
        min=0.0,
        max=1.0
    )
    
    # Material properties
    line_color: bpy.props.FloatVectorProperty(
        name="Line Color",
        description="Color of speed lines",
        default=(0.3, 0.7, 1.0),
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )
    
    emission_strength: bpy.props.FloatProperty(
        name="Emission Strength",
        description="Brightness of speed lines",
        default=3.0,
        min=0.0,
        max=10.0
    )
    
    use_transparency: bpy.props.BoolProperty(
        name="Use Transparency",
        description="Enable alpha blending for speed lines",
        default=True
    )
    
    replace_existing: bpy.props.BoolProperty(
        name="Replace Existing",
        description="Replace existing speed lines",
        default=True
    )

class SPEEDLINES_PT_panel(bpy.types.Panel):
    """Animated Speed Lines Panel"""
    bl_label = "Animated Speed Lines"
    bl_idname = "SPEEDLINES_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Speed Lines"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.speedlines_props
        
        # Generation button
        layout.operator("speedlines.generate", text="Generate Animated Speed Lines", icon='PLAY')
        layout.prop(props, "replace_existing")
        
        # Info about new behavior
        info_box = layout.box()
        info_box.label(text="💡 How it works:", icon='INFO')
        col = info_box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• Lines spawn randomly over time")
        col.label(text="• Each line moves forward once & disappears")
        col.label(text="• No cycling back - natural flowing effect")
        
        # Continuous flow setup
        layout.separator()
        box = layout.box()
        box.label(text="Random Spawning Flow", icon='LOOP_FORWARDS')
        box.operator("speedlines.continuous_flow", text="Setup Random Forward Flow", icon='CON_FOLLOWTRACK')
        
        layout.separator()
        
        # Zone settings
        box = layout.box()
        box.label(text="Zone Settings", icon='MESH_PLANE')
        box.prop(props, "zone_center")
        box.prop(props, "zone_size")
        
        # Animation settings
        box = layout.box()
        box.label(text="Speed & Animation", icon='TIME')
        
        # Speed presets
        box.label(text="Quick Presets:", icon='PRESET')
        row = box.row()
        op = row.operator("speedlines.speed_preset", text="Slow")
        op.preset_type = 'SLOW'
        op = row.operator("speedlines.speed_preset", text="Fast")
        op.preset_type = 'FAST'
        op = row.operator("speedlines.speed_preset", text="Bullet Time")
        op.preset_type = 'BULLET_TIME'
        
        box.separator()
        
        # Duration and speed controls
        box.label(text="Animation Timing:", icon='SETTINGS')
        box.prop(props, "animation_duration")
        
        row = box.row()
        row.prop(props, "speed_units_per_second")
        row.prop(props, "animation_speed")
        
        box.prop(props, "flow_direction")
        box.prop(props, "cycle_length")
        box.prop(props, "spawn_randomness")
        
        # Line settings
        box = layout.box()
        box.label(text="Line Settings", icon='CURVE_PATH')
        box.prop(props, "line_count")
        box.prop(props, "line_length")
        box.prop(props, "line_width")
        box.prop(props, "line_type")
        
        if props.line_type in ['TAPERED', 'TUBE']:
            box.prop(props, "taper_factor")
        
        # Pattern settings
        box = layout.box()
        box.label(text="Pattern", icon='MOD_ARRAY')
        box.prop(props, "pattern")
        
        if props.pattern == 'RADIAL':
            box.prop(props, "min_distance")
        elif props.pattern == 'PARALLEL':
            box.prop(props, "spacing")
        
        # Variation settings
        box = layout.box()
        box.label(text="Variation", icon='RNDCURVE')
        box.prop(props, "randomness")
        box.prop(props, "length_variation")
        
        # Material settings
        box = layout.box()
        box.label(text="Appearance", icon='MATERIAL')
        box.prop(props, "line_color")
        box.prop(props, "emission_strength")
        box.prop(props, "use_transparency")

class SPEEDLINES_PT_control_panel(bpy.types.Panel):
    """Speed Lines Control Panel"""
    bl_label = "Live Controls"
    bl_idname = "SPEEDLINES_PT_control_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        return (context.object and 
                context.object.name == "SpeedLines_Controller")
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        col = layout.column()
        col.label(text="Live Speed Line Controls", icon='FORCE_WIND')
        
        col.separator()
        
        if "animation_duration" in obj:
            col.prop(obj, '["animation_duration"]', text="Animation Duration")
        if "speed_units_per_second" in obj:
            col.prop(obj, '["speed_units_per_second"]', text="Speed (Units/Sec)")
        if "animation_speed" in obj:
            col.prop(obj, '["animation_speed"]', text="Speed Multiplier")
        if "flow_direction_x" in obj:
            col.label(text="Flow Direction:")
            row = col.row()
            row.prop(obj, '["flow_direction_x"]', text="X")
            row.prop(obj, '["flow_direction_y"]', text="Y")
            row.prop(obj, '["flow_direction_z"]', text="Z")
        if "cycle_length" in obj:
            col.prop(obj, '["cycle_length"]', text="Spawn Stagger")
        if "spawn_randomness" in obj:
            col.prop(obj, '["spawn_randomness"]', text="Spawn Randomness")

def register():
    bpy.utils.register_class(SpeedLinesProperties)
    bpy.utils.register_class(SPEEDLINES_OT_speed_preset)
    bpy.utils.register_class(SPEEDLINES_OT_continuous_flow)
    bpy.utils.register_class(SPEEDLINES_OT_generate)
    bpy.utils.register_class(SPEEDLINES_PT_panel)
    bpy.utils.register_class(SPEEDLINES_PT_control_panel)
    bpy.types.Scene.speedlines_props = bpy.props.PointerProperty(type=SpeedLinesProperties)

def unregister():
    bpy.utils.unregister_class(SpeedLinesProperties)
    bpy.utils.unregister_class(SPEEDLINES_OT_speed_preset)
    bpy.utils.unregister_class(SPEEDLINES_OT_continuous_flow)
    bpy.utils.unregister_class(SPEEDLINES_OT_generate)
    bpy.utils.unregister_class(SPEEDLINES_PT_panel)
    bpy.utils.unregister_class(SPEEDLINES_PT_control_panel)
    del bpy.types.Scene.speedlines_props

if __name__ == "__main__":
    register()