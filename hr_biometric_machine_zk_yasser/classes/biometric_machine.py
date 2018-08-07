from openerp.osv import fields, osv
from openerp import SUPERUSER_ID
from datetime import datetime , timedelta
import pytz
#from zklib import zklib
import time
#from zklib import zkconst

import zklib
import time

class biometric_machine(osv.Model):
    _name= 'biometric.machine.location'
    _columns = {
        'name' : fields.char("Location",required=True),
    }


class biometric_machine(osv.Model):
    _name= 'biometric.machine'
    _columns = {
        'name' : fields.char("Machine IP"),
        'location_id' : fields.many2one('biometric.machine.location',string="Location"),
        'port': fields.integer("Port Number"),
        'state': fields.selection([('draft','Draft'),('done','Done')],'State'),
    }


    def download_attendance(self, cr, uid, ids, context=None):
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, SUPERUSER_ID, uid)
        tz = pytz.timezone(user.partner_id.tz) or False
        if not tz:
            raise osv.except_osv('Error', "Timezone is not defined on this %s user." % user.name)

        
        machine_ip = self.browse(cr,uid,ids).name
        port = self.browse(cr,uid,ids).port
        location_id = self.browse(cr,uid,ids).location_id

        zk = zklib.ZKLib(machine_ip, int(port))
        res,error_str = zk.connect()
        aclog = ''
        
        if res == True:
            zk.enableDevice()
            zk.disableDevice()
            attendance=[]
            Done = False
            while not Done:
                attendance_new = zk.getAttendance()
                if (attendance_new):
                    for lattendance in attendance_new:
                        if lattendance[0] == '':
                            Done = True
                            break
                        attendance.append(lattendance)
            
            hr_attendance =  self.pool.get("hr.attendance")
            hr_employee = self.pool.get("hr.employee")
            hr_employee_zk_location_line_obj = self.pool.get("biometric.machine.zk_location.line")
            for lattendance in attendance:
                time_att = str(lattendance[2].date()) + ' ' +str(lattendance[2].time())
                aclog = lattendance[1]          
                atten_time1 = datetime.strptime(str(time_att), '%Y-%m-%d %H:%M:%S')
                atten_time_localize = pytz.utc.localize(atten_time1).astimezone(tz)
                #print atten_time_localize.hour-atten_time1.hour
                #if atten_time_localize.hour-atten_time1.hour >=0:
                atten_time = atten_time1 - (timedelta(hours=atten_time_localize.hour-atten_time1.hour))
                atten_time = datetime.strftime(atten_time,'%Y-%m-%d %H:%M:%S')
                #atten_time1 = datetime.strftime(atten_time1,'%Y-%m-%d %H:%M:%S')
                #in_time = datetime.strptime(atten_time1,'%Y-%m-%d %H:%M:%S').time()
                hr_employee_zk_location_line_id=hr_employee_zk_location_line_obj.search(cr,uid,[("zk_num", "=", str(lattendance[0])),('location_id.id','=',location_id.id)])
                hr_employee_zk_location_line_rec = hr_employee_zk_location_line_obj.browse(cr,uid,hr_employee_zk_location_line_id,context)
                #print hr_employee_zk_location_line_rec
                employee_id = hr_employee_zk_location_line_rec.emp_id.id or False
                #print employee_id
                #employee_id = hr_employee.search(cr,uid,[("zk_num", "=", str(lattendance[0])),('location_id.id','=',location_id.id)])
                address_id = False
                category = False
                if employee_id:
                    try:
                        atten_ids = hr_attendance.search(cr,uid,[('employee_id','=',employee_id),('name','=',atten_time)])
                        if atten_ids:
                            continue
                        else:
                            atten_id = hr_attendance.create(cr,uid,{'name':atten_time,'day':str(lattendance[2].date()),'employee_id':employee_id,'action':aclog})
                    except Exception,e:
                        pass
            zk.enableDevice()
            zk.disconnect()
            return True
        else:
            raise osv.except_osv(('Warning !'),("Unable to connect, please check the parameters and network connections because of error %s",error_str))
    '''
    def clear_attendance(self, cr, uid, ids, context=None):
        machine_ip = self.browse(cr,uid,ids).name
        port = self.browse(cr,uid,ids).port
        zk = zklib.ZKLib(machine_ip, int(port))
        res = zk.connect()
        if res == True:
            zk.enableDevice()
            zk.disableDevice()
            res = zk.clearAttendance()
            zk.enableDevice()
            zk.disconnect()
            return True
        else:
            raise osv.except_osv(('Warning !'),("Unable to connect, please check the parameters and network connections."))
     '''
class hr_employee(osv.Model):
    _inherit = 'hr.employee'
    _columns = {
        # 'zk_num': fields.integer(string="ZKSoftware Number", help="ZK Attendance User Code"),
        # 'location_id' : fields.many2one('biometric.machine.location',string="Location"),
        'zk_location_line_ids' : fields.one2many('biometric.machine.zk_location.line','emp_id',string='Zk Configuration'),
    }

class hr_employee_zk_location_line(osv.Model):
    _name = 'biometric.machine.zk_location.line'
    _columns = {
        'zk_num': fields.integer(string="ZKSoftware Number", help="ZK Attendance User Code",required=True),
        'location_id' : fields.many2one('biometric.machine.location',string="Location",required=True),
        'emp_id' : fields.many2one('hr.employee',string="Employee"),
        'emp_location' : fields.char(string='Employee per Location'),
        'zk_location' : fields.char(string='Zk per Location'),
    }
    _sql_constraints = [('unique_location_emp', 'unique(emp_location)', 'A record with the same location per employee exists.'),
                        ('unique_location_zk', 'unique(zk_location)', 'A record with the same zk in location exists.')]

    def onchange_location_id(self, cr, uid, ids, location_id,zk_num,context=None):
        res = {}
        warn = {}
        emp_pool = self.pool.get('hr.employee')
        emp_id = self.browse(cr,uid,ids,context).emp_id.id
        #print location_id,zk_num,emp_id
        location_pool = self.pool.get('biometric.machine.location')
        if location_id and emp_id:
            employee_name = emp_pool.browse(cr,uid,emp_id,context).name
            location_name = location_pool.browse(cr,uid,location_id,context).name
            res['emp_location'] = employee_name+location_name

        if location_id and zk_num:
            location_name = location_pool.browse(cr,uid,location_id,context).name
            res['zk_location'] = location_name+str(zk_num)

        return {'value': res, 'warning': warn}
    def create(self, cr, uid, values, context=None):
        emp_id = values.get('emp_id','')
        location_id = values.get('location_id','')
        zk_num = values.get('zk_num','')
        emp_pool = self.pool.get('hr.employee')
        location_pool = self.pool.get('biometric.machine.location')
        employee_name = emp_pool.browse(cr,uid,emp_id,context).name
        location_name = location_pool.browse(cr,uid,location_id,context).name
        values['emp_location'] = employee_name+location_name
        values['zk_location'] = location_name+str(zk_num)
        #print values['emp_location']
        #print values['zk_location']
        res = super(hr_employee_zk_location_line, self).create(cr, uid, values, context=context)
        return res