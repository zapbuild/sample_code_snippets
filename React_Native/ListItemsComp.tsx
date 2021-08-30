import React from 'react'
import {
    Text,
    StyleSheet,
    ViewStyle,
    TextStyle,
    View,
    TouchableOpacity
} from 'react-native'
import LinearGradient from 'react-native-linear-gradient';
import { moderateScale } from 'react-native-size-matters';
import { getIcons } from '../../assets/icons';
import { IconTypes } from '../../assets/Images';
import { capitalizeString, windowWidth } from '../../utils/Common';
import Config from '../../utils/Config';

// Component Props
interface Props {
    title: string;
    gradientColors?: Array<string>;
    containerStyle?: ViewStyle;
    textStyle?: TextStyle;
    iconName: IconTypes;
    iconSize?: number;
    showStatus?: boolean;
    onPress?: () => void;
    rightIcon?: IconTypes;
    onEditPress?: () => void;
}

// Return Flatlist item for Home Screen Sets list
const ListItemComp = ({
    title,
    containerStyle,
    textStyle,
    iconName,
    iconSize,
    rightIcon,
    gradientColors,
    onEditPress,
    onPress,
}: Props) => {

    return (
        <LinearGradient
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            colors={gradientColors || [
                Config.colors.HEADER_COLOR_1,
                Config.colors.HEADER_COLOR_2
            ]}
            style={{
                ...styles.container,
                ...containerStyle
            }}>
            <TouchableOpacity onPress={onPress}
                style={styles.container}
                activeOpacity={0.5}>
                <TouchableOpacity onPress={onEditPress}
                    style={styles.icon_style}>
                    {rightIcon ? getIcons(rightIcon, moderateScale(16)) : null}
                </TouchableOpacity>
                <Text
                    numberOfLines={3}
                    ellipsizeMode={'tail'}
                    style={[styles.headerText, textStyle]}>
                    {capitalizeString(title)}
                </Text>
                <View style={styles.iconStyle}>
                    {getIcons(iconName, iconSize ?? 110)}
                </View>
            </TouchableOpacity>
        </LinearGradient>
    )
}

const styles = StyleSheet.create({
    container: {
        width: windowWidth / 2.4,
        aspectRatio: 1.7,
        borderRadius: moderateScale(10),
        marginRight: moderateScale(10),
        justifyContent: 'center',
    },
    headerText: {
        color: 'white',
        fontFamily: Config.fonts.BOLD,
        fontSize: moderateScale(16),
        textAlign: 'center',
        paddingHorizontal: moderateScale(10)
    },
    iconStyle: {
        position: 'absolute',
        right: 0,
        bottom: -15
    },
    icon_style: {
        position: "absolute",
        padding: moderateScale(5),
        zIndex: 1,
        right: 10,
        top: -2
    }
})

export default ListItemComp;
