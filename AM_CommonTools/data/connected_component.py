
# ===============================================
# Class that represents a connected component
# inside of a sketch
#
# By: Kenny Davila
#     Rochester Institute of Technology
#     2013-2017
#
# Modified by:
#     Kenny Davila (April 18, 2014)
#       - Made it lighter by removing unneeded references...
#
# ===============================================

import cv2
import numpy as np
import math
import ctypes

class ConnectedComponent:
    NormalizedSize = 128
    MinScalingSize = 10

    def __init__(self, cc_id, min_x, max_x, min_y, max_y, size, img):
        # Spatial information
        self.cc_id = cc_id
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.size = size
        self.img = img

        self.normalized = None

        # Temporal information
        self.start_time = None
        self.end_time = None
        self.next_cc = None
        self.prev_cc = None

    def getBoundingBox(self):
        return (self.min_x, self.max_x), (self.min_y, self.max_y)

    def getBoxArea(self):
        return (self.max_x - self.min_x + 1) * (self.max_y - self.min_y + 1)

    def getBoxDiagonal(self):
        w = self.getWidth()
        h = self.getHeight()
        return math.sqrt(w * w + h * h)

    def getOverlapArea(self, other):
        assert isinstance(other, ConnectedComponent)

        # check if boxes overlap
        if ((self.min_x <= other.max_x and other.min_x <= self.max_x) and
            (self.min_y <= other.max_y and other.min_y <= self.max_y)):
            o_min_x = max(self.min_x, other.min_x)
            o_max_x = min(self.max_x, other.max_x)
            o_min_y = max(self.min_y, other.min_y)
            o_max_y = min(self.max_y, other.max_y)

            return (o_max_x - o_min_x + 1) * (o_max_y - o_min_y + 1)
        else:
            return 0.0

    def getContours(self):
        # add some padding first ...
        copy = cv2.copyMakeBorder(self.img, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=(0, ))
        # get the contour(s) ...
        if int(cv2.__version__.split(".")[0]) >= 4:
            raw_contours, _ = cv2.findContours(copy, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        else:
            _, raw_contours, _ = cv2.findContours(copy, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        resulting_contours = []
        for contour in raw_contours:
            # remove the extra dimension (x-values, ??, y-values)
            contour = contour.reshape((contour.shape[0], contour.shape[2]))
            # offset values to original space (remove padding as well)
            contour[:, 0] += (self.min_x - 2)
            contour[:, 1] += (self.min_y - 2)

            resulting_contours.append(contour)

        return resulting_contours

    @staticmethod
    def Merge(cc_list):
        all_cc_data = [(cc.cc_id, cc.min_x, cc.max_x, cc.min_y, cc.max_y) for cc in cc_list]
        ids, mins_x, maxs_x, mins_y, maxs_y = zip(*all_cc_data)

        merged_cc = ConnectedComponent(min(ids), min(mins_x), max(maxs_x), min(mins_y), max(maxs_y), None, None)

        # compute combined image (and its size in foreground pixels)
        w = merged_cc.getWidth()
        h = merged_cc.getHeight()
        combined_image = np.zeros((h, w), dtype=np.uint8)
        for cc in cc_list:
            start_y = cc.min_y - merged_cc.min_y
            end_y = cc.max_y - merged_cc.min_y + 1
            start_x = cc.min_x - merged_cc.min_x
            end_x = cc.max_x - merged_cc.min_x + 1
            cc_cut = combined_image[start_y:end_y, start_x:end_x]
            cc_cut[cc.img > 0] = 255

            #cv2.imshow("part - " + cc.strID(), cc.img)

        merged_cc.img = combined_image
        merged_cc.size = np.count_nonzero(combined_image)

        return merged_cc

    @staticmethod
    def MedianSize(cc_list):
        all_width = []
        all_heights = []
        for cc in cc_list:
            assert isinstance(cc, ConnectedComponent)

            all_width.append(cc.getWidth())
            all_heights.append(cc.getHeight())

        median_w = np.median(np.array(all_width))
        median_h = np.median(np.array(all_heights))

        return median_h, median_w

    @staticmethod
    def ShallowCopy(src):
        assert isinstance(src, ConnectedComponent)

        # only copy main attributes
        return ConnectedComponent(src.cc_id, src.min_x, src.max_x, src.min_y, src.max_y, src.size, src.img.copy())

    def strID(self):
        return "%d-%d-%d-%d-%d" % (self.min_x, self.max_x, self.min_y, self.max_y, self.size)

    def getEndTime(self):
        current = self
        while current.next_cc is not None:
            current = current.next_cc

        return current.end_time

    def getStartTime(self):
        current = self
        while current.prev_cc is not None:
            current = current.prev_cc

        return current.start_time

    def getCenterOfMass(self):
        y_vals, x_vals = self.img.nonzero()

        mass_y = self.min_y + int(round(y_vals.mean()))
        mass_x = self.min_x + int(round(x_vals.mean()))

        return mass_x, mass_y

    def translateBox(self, disp_x, disp_y):
        self.min_x += disp_x
        self.max_x += disp_x
        self.min_y += disp_y
        self.max_y += disp_y

    def getOverlapImage(self, other):
        # compute a bigger box containing both CC
        b_min_x = min(self.min_x, other.min_x)
        b_max_x = max(self.max_x, other.max_x)
        b_min_y = min(self.min_y, other.min_y)
        b_max_y = max(self.max_y, other.max_y)

        b_width = b_max_x - b_min_x + 1
        b_height = b_max_y - b_min_y + 1

        overlap_image = np.zeros((b_height, b_width, 3), dtype=np.uint8)

        # add local
        ls_x = (self.min_x - b_min_x)
        ls_y = (self.min_y - b_min_y)
        overlap_image[ls_y:ls_y + self.img.shape[0], ls_x:ls_x + self.img.shape[1], 2] = self.img.copy()

        # add other
        os_x = (other.min_x - b_min_x)
        os_y = (other.min_y - b_min_y)
        overlap_image[os_y:os_y + other.img.shape[0], os_x:os_x + other.img.shape[1], 1] = other.img.copy()

        return overlap_image

    def getOverlapIOU(self, other):
        # computes bounding boxes intersection over union ...
        area_int = self.getOverlapArea(other)
        area_local = self.getBoxArea()
        area_other = other.getBoxArea()
        area_union = area_local + area_other - area_int

        return area_int / area_union

    def getOverlapFMeasure(self, other, verbose=False, single_score=True):
        # first, must check if boxes overlap
        if (self.max_y >= other.min_y and other.max_y >= self.min_y and
            self.max_x >= other.min_x and other.max_x >= self.min_x):

            if verbose:
                print("overlap!")

            # only obtain the small overlapped box
            b_min_x = max(self.min_x, other.min_x)
            b_max_x = min(self.max_x, other.max_x)
            b_min_y = max(self.min_y, other.min_y)
            b_max_y = min(self.max_y, other.max_y)

            b_width = b_max_x - b_min_x + 1
            b_height = b_max_y - b_min_y + 1

            ls_x = (b_min_x - self.min_x)
            ls_y = (b_min_y - self.min_y)
            local_image = self.img[ls_y:ls_y + b_height, ls_x:ls_x + b_width]

            os_x = (b_min_x - other.min_x)
            os_y = (b_min_y - other.min_y)
            other_image = other.img[os_y:os_y + b_height, os_x:os_x + b_width]

            # match = np.bitwise_and(local_image, other_image).sum() / 255.0
            match = np.count_nonzero(np.bitwise_and(local_image, other_image))

            if verbose:
                print("Match: " + str(match))

            #norm_size = float(min(self.size, other.size))
            if single_score:
                overlap = (2.0 * match) / float(self.size + other.size)

                return overlap
            else:
                recall = match / float(self.size)
                precision = match / float(other.size)

                return recall, precision

        else:
            # if boxes do not overlap, no pixel does ...
            if verbose:
                print("No overlap")


            return 0.0 if single_score else (0.0, 0.0)

    def __str__(self):
        content = "ConnectedComponent -> Id = " + str(self.cc_id) + "\n"
        content += " -> X : [" + str(self.min_x) + ", " + str(self.max_x) + "] \n"
        content += " -> Y : [" + str(self.min_y) + ", " + str(self.max_y) + "]"

        return content

    def getCenterDistance(self, other):
        cx1, cy1 = self.getCenter()
        cx2, cy2 = other.getCenter()

        return math.sqrt( (cx1 - cx2) ** 2 + (cy1 - cy2) ** 2 )

    def getCenterDistanceWithOffset(self, other, local_offset, other_offset):
        cx1, cy1 = self.getCenter()
        cx2, cy2 = other.getCenter()

        cx1 += local_offset[0]
        cy1 += local_offset[1]

        cx2 += other_offset[0]
        cy2 += other_offset[1]

        return math.sqrt( (cx1 - cx2) ** 2 + (cy1 - cy2) ** 2 )

    def getCenter(self):
        cx = (self.min_x + self.max_x) / 2.0
        cy = (self.min_y + self.max_y) / 2.0

        return (cx, cy)

    def getWidth(self):
        return (self.max_x - self.min_x + 1)

    def getHeight(self):
        return (self.max_y - self.min_y + 1)

    def getBoxDistanceWithOffset(self, other, local_offset, other_offset):

        #first, check if boxes overlap, in such case the distance is 0.0
        if self.min_x + local_offset[0] <= other.max_x + other_offset[0] and \
           other.min_x + other_offset[0] <= self.max_x + local_offset[0] and \
           self.min_y + local_offset[1] <= other.max_y + other_offset[1] and \
           other.min_y + other_offset[1] <= self.max_y + local_offset[1]:
            #overlap, distance is 0.0
            return 0.0
        elif self.min_x + local_offset[0] <= other.max_x + other_offset[0] and \
           other.min_x + other_offset[0] <= self.max_x + local_offset[0]:
            #overlap on x but not on y, use y!
            if self.max_y + local_offset[1] > other.max_y + other_offset[1]:
                return (self.min_y + local_offset[1]) - (other.max_y + other_offset[1])
            else:
                return (other.min_y + other_offset[1]) - (self.max_y + local_offset[1])
        elif self.min_y + local_offset[1] <= other.max_y + other_offset[1] and \
           other.min_y + other_offset[1] <= self.max_y + local_offset[1]:
            #overlap on y but not on x, use x!
            if self.max_x + local_offset[0] > other.max_x + other_offset[0]:
                return (self.min_x + local_offset[0]) - (other.max_x + other_offset[0])
            else:
                return (other.min_x + other_offset[0]) - (self.max_x + local_offset[0])
        else:
            #no overlap at all, calculate the two distances
            #to find the minimum distance between the corners...
            if self.max_y + local_offset[1] > other.max_y + other_offset[1]:
                dist_y = (self.min_y + local_offset[1]) - (other.max_y + other_offset[1])
            else:
                dist_y = (other.min_y + other_offset[1]) - (self.max_y + local_offset[1])

            if self.max_x + local_offset[0] > other.max_x + other_offset[0]:
                dist_x = (self.min_x + local_offset[0]) - (other.max_x + other_offset[0])
            else:
                dist_x = (other.min_x + other_offset[0]) - (self.max_x + local_offset[0])

            return math.sqrt( dist_x * dist_x + dist_y * dist_y )

        return 0.0

    def getBoxDistance(self, other):
        # first, check if boxes overlap, in such case the distance is 0.0
        if self.min_x <= other.max_x and \
           other.min_x <= self.max_x and \
           self.min_y <= other.max_y and \
           other.min_y <= self.max_y:
            # overlap, distance is 0.0
            return 0.0
        elif self.min_x <= other.max_x and \
           other.min_x <= self.max_x:
            # overlap on x but not on y, use y!
            if self.max_y > other.max_y:
                return self.min_y - other.max_y
            else:
                return other.min_y - self.max_y
        elif self.min_y <= other.max_y and \
           other.min_y <= self.max_y:
            # overlap on y but not on x, use x!
            if self.max_x > other.max_x:
                return self.min_x - other.max_x
            else:
                return other.min_x - self.max_x
        else:
            # no overlap at all, calculate the two distances
            # to find the minimum distance between the corners...
            if self.max_y > other.max_y:
                dist_y = self.min_y - other.max_y
            else:
                dist_y = other.min_y - self.max_y

            if self.max_x > other.max_x:
                dist_x = self.min_x - other.max_x
            else:
                dist_x = other.min_x - self.max_x

            return math.sqrt( dist_x * dist_x + dist_y * dist_y )

        return 0.0

    def release(self):
        self.normalized = None

    def normalizeImage(self, new_size):
        # create a resized version of the image
        # with a predefined size

        # first, generate a squared version of original
        #...check longest to keep aspect ratio....
        longest = max(self.img.shape[0], self.img.shape[1])

        #...offset....
        offset_y = int((longest - self.img.shape[0]) / 2.0)
        offset_x = int((longest - self.img.shape[1]) / 2.0)

        #...check if padding is required...
        if longest < ConnectedComponent.MinScalingSize:
            padding = int(math.ceil( (ConnectedComponent.MinScalingSize - longest) / 2.0 ))
        else:
            padding = 0

        start_y = offset_y + padding
        start_x = offset_x + padding

        #...the final matrix...
        squared = np.zeros((longest + padding * 2, longest + padding * 2))

        # generate the squared version ...
        squared[ start_y:(start_y + self.img.shape[0]), start_x:(start_x + self.img.shape[1]) ] = self.img

        # now generate the scaled version
        #scaled = np.zeros((new_size, new_size))
        scaled = cv2.resize(squared, (new_size, new_size))

        self.normalized = cv2.compare(scaled, 128, cv2.CMP_GT)

