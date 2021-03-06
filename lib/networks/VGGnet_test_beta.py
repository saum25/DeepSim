import tensorflow as tf
from .network import Network
from ..fast_rcnn.config import cfg


class VGGnet_test(Network):
    def __init__(self, trainable=True, conv1_5_trainable=[False, False, False, False, False]):
        assert len(conv1_5_trainable) == 5
        self.inputs = []
        self.data = tf.placeholder(tf.float32, shape=[None, None, None, 3])
        # im_info: a list of [image_height, image_width, scale_ratios]
        self.im_info = tf.placeholder(tf.float32, shape=[None, 3])
        self.keep_prob = tf.placeholder(tf.float32)
        self.layers = dict({'data': self.data, 'im_info': self.im_info})
        self.trainable = trainable
        self.setup(conv1_5_trainable)

    def setup(self, conv1_5_trainable):
        # n_classes = 21
        n_classes = cfg.NCLASSES
        self.n_classes = n_classes
        # anchor_scales = [8, 16, 32]
        anchor_scales = cfg.ANCHOR_SCALES
        _feat_stride = [16, ]

        trainable_to_forked = False
        (self.feed('data')
         .conv(3, 3, 64, 1, 1, name='conv1_1', trainable=conv1_5_trainable[0])
         .conv(3, 3, 64, 1, 1, name='conv1_2', trainable=conv1_5_trainable[0])
         .max_pool(2, 2, 2, 2, padding='VALID', name='pool1')
         .conv(3, 3, 128, 1, 1, name='conv2_1', trainable=conv1_5_trainable[1])
         .conv(3, 3, 128, 1, 1, name='conv2_2', trainable=conv1_5_trainable[1])
         .max_pool(2, 2, 2, 2, padding='VALID', name='pool2')
         .conv(3, 3, 256, 1, 1, name='conv3_1', trainable=conv1_5_trainable[2])
         .conv(3, 3, 256, 1, 1, name='conv3_2', trainable=conv1_5_trainable[2])
         .conv(3, 3, 256, 1, 1, name='conv3_3', trainable=conv1_5_trainable[2])
         .max_pool(2, 2, 2, 2, padding='VALID', name='pool3')
         .conv(3, 3, 512, 1, 1, name='conv4_1', trainable=conv1_5_trainable[3])
         .conv(3, 3, 512, 1, 1, name='conv4_2', trainable=conv1_5_trainable[3])
         .conv(3, 3, 512, 1, 1, name='conv4_3', trainable=conv1_5_trainable[3])
         .max_pool(2, 2, 2, 2, padding='VALID', name='pool4')
         .conv(3, 3, 512, 1, 1, name='conv5_1', trainable=conv1_5_trainable[4])
         .conv(3, 3, 512, 1, 1, name='conv5_2', trainable=conv1_5_trainable[4])
         .conv(3, 3, 512, 1, 1, name='conv5_3', trainable=conv1_5_trainable[4]))

        (self.feed('conv5_3')
         .conv(3, 3, 512, 1, 1, name='rpn_conv/3x3', trainable=False)
         .conv(1, 1, len(anchor_scales) * 3 * 2, 1, 1, padding='VALID', relu=False, name='rpn_cls_score', trainable=False))

        (self.feed('rpn_conv/3x3')
         .conv(1, 1, len(anchor_scales) * 3 * 4, 1, 1, padding='VALID', relu=False, name='rpn_bbox_pred', trainable=False))

        # H is current height, W is current width. A is anchor number = 9.
        #  shape is (1, H, W, Ax2) -> (1, H, WxA, 2)
        (self.feed('rpn_cls_score')
         .spatial_reshape_layer(2, name='rpn_cls_score_reshape')
         .spatial_softmax(name='rpn_cls_prob'))

        # shape is (1, H, WxA, 2) -> (1, H, W, Ax2)
        (self.feed('rpn_cls_prob')
         .spatial_reshape_layer(len(anchor_scales) * 3 * 2, name='rpn_cls_prob_reshape'))

        (self.feed('rpn_cls_prob_reshape', 'rpn_bbox_pred', 'im_info')
         .proposal_layer(_feat_stride, anchor_scales, 'TEST', name='rois'))

        #(self.feed('conv5_3', 'rois')
        #.roi_pool(7, 7, 1.0 / 16, name='pool_5')
        #.fc(4096, name='fc6', trainable=False)
        #.fc(4096, name='fc7', trainable=False)
        #.fc(n_classes, activation=None, name='cls_score', trainable=False)
        #.softmax(name='cls_prob'))

        #(self.feed('fc7')
        #.fc(n_classes * 4, activation=None, name='bbox_pred', trainable=False))

