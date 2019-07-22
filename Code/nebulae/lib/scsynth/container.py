#   Copyright (C) 2006 by Patrick Stinson                                 
#   patrickkidd@gmail.com                                                   
#                                                                         
#   This program is free software; you can redistribute it and/or modify  
#   it under the terms of the GNU General Public License as published by  
#   the Free Software Foundation; either version 2 of the License, or     
#   (at your option) any later version.                                   
#                                                                         
#   This program is distributed in the hope that it will be useful,       
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
#   GNU General Public License for more details.                          
#                                                                         
#   You should have received a copy of the GNU General Public License     
#   along with this program; if not, write to the                         
#   Free Software Foundation, Inc.,                                       
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.  
#
"""
Container look-alike
"""

class ContainerProxyBase(object):
    """ A container look-alike without inheriting a built-in type.
    This resolves conflicts related to inheriting multiple C types.
    """
    def __init__(self, data):
        self.container = data
    def __getitem__(self, key):
        return self.container.__getitem__(key)
    def __setitem__(self, key, value):
        return self.container.__setitem__(key, value)
    def __delitem__(self, key):
        return self.container.__delitem__(key)
    def __iter__(self):
        return self.container.__iter__()
    def __len__(self):
        return self.container.__len__()
    def __contains__(self, item):
        return self.container.__contains__(item)
    def __str__(self):
        return self.container.__str__()
    def __repr__(self):
        return self.container.__repr__()


class ListProxy(ContainerProxyBase):
    def __init__(self):
        ContainerProxyBase.__init__(self, [])
        self.append = self.container.append
        self.remove = self.container.remove
        self.sort = self.container.sort


class DictProxy(ContainerProxyBase):
    def __init__(self):
        ContainerProxyBase.__init__(self, {})
        self.items = self.container.items
        self.udpate = self.container.update
#        self.copy = self.container.copy
